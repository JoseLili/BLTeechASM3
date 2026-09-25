"""Production arbitration for the three direct carrier buttons."""

from __future__ import annotations

from typing import Protocol

from asm.application.ports import ClockPort, EventLogRepository
from asm.domain.models import AuditRecord, StateTransition
from asm.domain.same import SameEventCode
from asm.domain.states import EventSource, EventType, SystemState
from asm.domain.transitions import InvalidTransition, transition


class LocalEventPresenter(Protocol):
    """Narrow SAME/output coordinator surface needed by the button panel."""

    @property
    def active_local_event(self) -> EventType | None: ...

    @property
    def active_same_event(self) -> SameEventCode | None: ...

    def start_local_event(self, event: EventType) -> bool: ...

    def stop_local_event(self) -> bool: ...


_LOCAL_STATES = {
    EventType.START_SIMULACRO: SystemState.SIMULACRO_ACTIVE,
    EventType.START_EVACUACION: SystemState.EVACUACION_ACTIVE,
}


class ProductionPanelController:
    """Audit local commands while preserving radio EQW as the top priority."""

    def __init__(
        self,
        *,
        messages: LocalEventPresenter,
        clock: ClockPort,
        event_log: EventLogRepository,
    ) -> None:
        self._messages = messages
        self._clock = clock
        self._event_log = event_log

    @property
    def state(self) -> SystemState:
        local = self._messages.active_local_event
        if local is not None:
            return _LOCAL_STATES[local]
        same = self._messages.active_same_event
        if same is SameEventCode.EQW:
            return SystemState.EQW_ACTIVE
        if same is SameEventCode.RWT:
            return SystemState.RWT_ACTIVE
        return SystemState.IDLE

    def dispatch(
        self,
        event: EventType,
        *,
        source: EventSource = EventSource.SYSTEM,
    ) -> StateTransition:
        """Apply one physical-panel command and persist its decision."""
        if event not in (*_LOCAL_STATES, EventType.STOP_REQUESTED):
            raise ValueError(f"unsupported production panel event: {event}")

        previous = self.state
        if event is EventType.STOP_REQUESTED and self._messages.active_local_event is None:
            self._reject(event, source, previous, "no local activation to stop")

        try:
            result = transition(previous, event)
        except InvalidTransition:
            self._reject(event, source, previous, "blocked by active event priority")

        accepted = (
            self._messages.stop_local_event()
            if event is EventType.STOP_REQUESTED
            else self._messages.start_local_event(event)
        )
        if not accepted:
            self._reject(event, source, previous, "output coordinator rejected command")

        self._event_log.append(
            AuditRecord(
                occurred_at=self._clock.now(),
                event=event,
                source=source,
                previous_state=previous,
                resulting_state=result.resulting_state,
                accepted=True,
                reason="local panel command accepted",
            )
        )
        return result

    def _reject(
        self,
        event: EventType,
        source: EventSource,
        previous: SystemState,
        reason: str,
    ) -> None:
        self._event_log.append(
            AuditRecord(
                occurred_at=self._clock.now(),
                event=event,
                source=source,
                previous_state=previous,
                resulting_state=None,
                accepted=False,
                reason=reason,
            )
        )
        raise InvalidTransition(previous, event)
