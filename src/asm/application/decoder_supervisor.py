"""Restart supervision for the continuous external SAME decoder pipeline."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum

from asm.application.ports import SameDecoderStreamPort


class DecoderServiceState(StrEnum):
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    BACKOFF = "BACKOFF"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class DecoderCycle:
    state: DecoderServiceState
    lines: tuple[str, ...] = ()
    error: str | None = None
    retry_in_seconds: float = 0.0


class DecoderSupervisor:
    """Keep a decoder stream alive with bounded exponential restart delay."""

    def __init__(
        self,
        *,
        stream_factory: Callable[[], SameDecoderStreamPort],
        monotonic: Callable[[], float],
        initial_retry_seconds: float = 1.0,
        maximum_retry_seconds: float = 30.0,
        stable_reset_seconds: float = 60.0,
    ) -> None:
        if initial_retry_seconds <= 0:
            raise ValueError("initial_retry_seconds must be greater than zero")
        if maximum_retry_seconds < initial_retry_seconds:
            raise ValueError("maximum_retry_seconds must not be less than initial retry")
        if stable_reset_seconds <= 0:
            raise ValueError("stable_reset_seconds must be greater than zero")
        self._stream_factory = stream_factory
        self._monotonic = monotonic
        self._initial_retry_seconds = initial_retry_seconds
        self._maximum_retry_seconds = maximum_retry_seconds
        self._stable_reset_seconds = stable_reset_seconds
        self._stream: SameDecoderStreamPort | None = None
        self._started_at: float | None = None
        self._next_start_at = 0.0
        self._failure_count = 0

    def poll(self) -> DecoderCycle:
        now = self._monotonic()
        if self._stream is None:
            if now < self._next_start_at:
                return DecoderCycle(
                    state=DecoderServiceState.BACKOFF,
                    retry_in_seconds=self._next_start_at - now,
                )
            return self._start(now)

        if self._started_at is not None and now - self._started_at >= self._stable_reset_seconds:
            self._failure_count = 0
        try:
            lines = self._stream.poll_lines()
        except Exception as error:
            return self._fail(now, error)
        return DecoderCycle(state=DecoderServiceState.RUNNING, lines=lines)

    def close(self) -> None:
        stream = self._stream
        self._stream = None
        self._started_at = None
        if stream is not None:
            stream.stop()

    def _start(self, now: float) -> DecoderCycle:
        stream = self._stream_factory()
        try:
            stream.start()
        except Exception as error:
            with suppress(Exception):
                stream.stop()
            return self._schedule_failure(now, error)
        self._stream = stream
        self._started_at = now
        return DecoderCycle(state=DecoderServiceState.STARTED)

    def _fail(self, now: float, error: Exception) -> DecoderCycle:
        stream = self._stream
        self._stream = None
        self._started_at = None
        if stream is not None:
            with suppress(Exception):
                stream.stop()
        return self._schedule_failure(now, error)

    def _schedule_failure(self, now: float, error: Exception) -> DecoderCycle:
        retry = self._initial_retry_seconds
        for _attempt in range(self._failure_count):
            retry = min(retry * 2, self._maximum_retry_seconds)
            if retry >= self._maximum_retry_seconds:
                break
        self._failure_count += 1
        self._next_start_at = now + retry
        return DecoderCycle(
            state=DecoderServiceState.FAILED,
            error=str(error) or type(error).__name__,
            retry_in_seconds=retry,
        )
