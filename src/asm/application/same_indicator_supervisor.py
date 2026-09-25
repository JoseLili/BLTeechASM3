"""Application service joining decoded SAME lines to timed panel indication."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum

from asm.application.indicator_policy import indicator_state_for
from asm.application.ports import IndicatorPort
from asm.domain.indicators import IndicatorState
from asm.domain.same import (
    SameEndOfMessage,
    SameEventCode,
    SameHeader,
    SameIndicatorSnapshot,
    SameNoticeReceipt,
    SameNoticeTracker,
    SameParseError,
    parse_multimon_same_line,
)
from asm.domain.states import EventType, SystemState


class SameLineOutcome(StrEnum):
    IGNORED = "IGNORED"
    INVALID = "INVALID"
    END_OF_MESSAGE = "END_OF_MESSAGE"
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


class SameIndicatorSupervisor:
    """Own SAME indication updates while leaving audit policy to its caller."""

    def __init__(
        self,
        *,
        indicators: IndicatorPort,
        monotonic: Callable[[], float],
        blink_half_period_seconds: float = 1.0,
        duplicate_window_seconds: float = 10.0,
    ) -> None:
        self._indicators = indicators
        self._monotonic = monotonic
        self._tracker = SameNoticeTracker(
            blink_half_period_seconds=blink_half_period_seconds,
            duplicate_window_seconds=duplicate_window_seconds,
        )
        self._local_event: EventType | None = None
        self._last_indicators: IndicatorState | None = None

    def set_local_event(self, event: EventType | None) -> None:
        """Overlay a local activation unless an EQW currently has priority."""
        if event not in (
            None,
            EventType.START_SIMULACRO,
            EventType.START_EVACUACION,
        ):
            raise ValueError("local event must be Simulacro, Evacuacion, or None")
        if event is self._local_event:
            return
        self._local_event = event
        self.apply_snapshot(self.snapshot())

    def handle_line(self, line: str) -> SameLineOutcome:
        """Consume one decoder line; invalid candidates fail closed."""
        try:
            decoded = parse_multimon_same_line(line)
        except SameParseError:
            return SameLineOutcome.INVALID
        if decoded is None:
            return SameLineOutcome.IGNORED
        if isinstance(decoded, SameEndOfMessage):
            return SameLineOutcome.END_OF_MESSAGE

        return self._accept_header(decoded)

    def handle_header(self, header: SameHeader) -> SameLineOutcome:
        """Accept one already-parsed header without reparsing its raw text."""
        outcome = self.track_header(header)
        self.poll()
        return outcome

    def track_header(self, header: SameHeader) -> SameLineOutcome:
        """Update notice validity without applying panel outputs yet."""
        receipt = self._tracker.receive(header, received_at=self._monotonic())
        if receipt is SameNoticeReceipt.DUPLICATE:
            return SameLineOutcome.DUPLICATE
        return SameLineOutcome.ACCEPTED

    def snapshot(self) -> SameIndicatorSnapshot:
        """Read current notice state without touching physical indicators."""
        return self._tracker.snapshot(now=self._monotonic())

    def apply_snapshot(self, snapshot: SameIndicatorSnapshot) -> None:
        """Apply a previously inspected snapshot to the physical panel."""
        effective = snapshot.indicators
        if snapshot.event is not SameEventCode.EQW and self._local_event is not None:
            local_state = (
                SystemState.SIMULACRO_ACTIVE
                if self._local_event is EventType.START_SIMULACRO
                else SystemState.EVACUACION_ACTIVE
            )
            effective = indicator_state_for(local_state)
        if effective != self._last_indicators:
            self._indicators.apply(effective)
            self._last_indicators = effective

    def poll(self) -> SameIndicatorSnapshot:
        """Advance blink/expiry state without blocking the application loop."""
        snapshot = self.snapshot()
        self.apply_snapshot(snapshot)
        return snapshot

    def _accept_header(self, header: SameHeader) -> SameLineOutcome:
        outcome = self.track_header(header)
        self.poll()
        return outcome
