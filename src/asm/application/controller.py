"""Application orchestration for system state changes."""

from __future__ import annotations

from asm.application.indicator_policy import indicator_state_for
from asm.application.ports import (
    ClockPort,
    DisplayPort,
    EventLogRepository,
    IndicatorPort,
    SystemView,
)
from asm.domain.models import AuditRecord, StateTransition
from asm.domain.states import EventType, SystemState
from asm.domain.transitions import InvalidTransition, transition

_VIEWS: dict[SystemState, tuple[str, str]] = {
    SystemState.BOOT: ("ASM BLTeech", "Iniciando"),
    SystemState.SELF_TEST: ("Autoprueba", "Verificando sistema"),
    SystemState.IDLE: ("Sistema listo", "En espera"),
    SystemState.SIMULACRO_ACTIVE: ("SIMULACRO", "Evento activo"),
    SystemState.STOPPED: ("Evento detenido", "Paro registrado"),
}


class SystemController:
    """Coordinate pure transitions with display and audit ports."""

    def __init__(
        self,
        *,
        clock: ClockPort,
        display: DisplayPort,
        event_log: EventLogRepository,
        indicators: IndicatorPort,
    ) -> None:
        self._clock = clock
        self._display = display
        self._event_log = event_log
        self._indicators = indicators
        self._state = SystemState.BOOT

    @property
    def state(self) -> SystemState:
        return self._state

    def present(self) -> None:
        """Render the current state without changing it."""
        title, detail = _VIEWS[self._state]
        self._indicators.apply(indicator_state_for(self._state))
        self._display.show(SystemView(state=self._state, title=title, detail=detail))

    def dispatch(self, event: EventType) -> StateTransition:
        """Apply one event, audit the decision, and update the display."""
        previous_state = self._state
        try:
            result = transition(previous_state, event)
        except InvalidTransition:
            self._event_log.append(
                AuditRecord(
                    occurred_at=self._clock.now(),
                    event=event,
                    previous_state=previous_state,
                    resulting_state=None,
                    accepted=False,
                    reason="invalid transition",
                )
            )
            raise

        self._state = result.resulting_state
        self._event_log.append(
            AuditRecord(
                occurred_at=self._clock.now(),
                event=event,
                previous_state=previous_state,
                resulting_state=self._state,
                accepted=True,
                reason="transition accepted",
            )
        )
        self.present()
        return result
