from __future__ import annotations

from dataclasses import dataclass, field

from asm.application.decoder_supervisor import DecoderServiceState, DecoderSupervisor


@dataclass
class ManualMonotonic:
    current: float = 0.0

    def __call__(self) -> float:
        return self.current


@dataclass
class FakeStream:
    start_error: Exception | None = None
    poll_results: list[tuple[str, ...] | Exception] = field(default_factory=list)
    starts: int = 0
    stops: int = 0

    def start(self) -> None:
        self.starts += 1
        if self.start_error is not None:
            raise self.start_error

    def poll_lines(self) -> tuple[str, ...]:
        if not self.poll_results:
            return ()
        result = self.poll_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def stop(self) -> None:
        self.stops += 1


def test_supervisor_starts_and_returns_nonblocking_lines() -> None:
    clock = ManualMonotonic()
    stream = FakeStream(poll_results=[("EAS: NNNN",)])
    supervisor = DecoderSupervisor(stream_factory=lambda: stream, monotonic=clock)

    assert supervisor.poll().state is DecoderServiceState.STARTED
    cycle = supervisor.poll()

    assert cycle.state is DecoderServiceState.RUNNING
    assert cycle.lines == ("EAS: NNNN",)


def test_failures_back_off_exponentially_and_create_fresh_streams() -> None:
    clock = ManualMonotonic()
    streams: list[FakeStream] = []

    def factory() -> FakeStream:
        stream = FakeStream(start_error=RuntimeError("capture unavailable"))
        streams.append(stream)
        return stream

    supervisor = DecoderSupervisor(stream_factory=factory, monotonic=clock)

    first = supervisor.poll()
    assert first.state is DecoderServiceState.FAILED
    assert first.retry_in_seconds == 1
    clock.current = 0.5
    assert supervisor.poll().state is DecoderServiceState.BACKOFF
    clock.current = 1.0
    second = supervisor.poll()
    assert second.state is DecoderServiceState.FAILED
    assert second.retry_in_seconds == 2
    assert len(streams) == 2
    assert all(stream.stops == 1 for stream in streams)


def test_running_failure_stops_stream_and_recovers_after_delay() -> None:
    clock = ManualMonotonic()
    first = FakeStream(poll_results=[RuntimeError("multimon stopped")])
    second = FakeStream()
    streams = iter((first, second))
    supervisor = DecoderSupervisor(stream_factory=lambda: next(streams), monotonic=clock)
    supervisor.poll()

    failure = supervisor.poll()
    assert failure.state is DecoderServiceState.FAILED
    assert first.stops == 1
    clock.current = 1.0
    assert supervisor.poll().state is DecoderServiceState.STARTED
    assert second.starts == 1
