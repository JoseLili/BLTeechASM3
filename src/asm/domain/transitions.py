"""Pure transition rules for the first state-machine slice."""

from __future__ import annotations

from asm.domain.models import StateTransition
from asm.domain.states import EventType, SystemState


class InvalidTransition(ValueError):
    """Raised when an event is not valid for the current state."""

    def __init__(self, state: SystemState, event: EventType) -> None:
        self.state = state
        self.event = event
        super().__init__(f"{event} is not valid from {state}")


_TRANSITIONS: dict[tuple[SystemState, EventType], SystemState] = {
    (SystemState.BOOT, EventType.BOOT_COMPLETED): SystemState.SELF_TEST,
    (SystemState.SELF_TEST, EventType.SELF_TEST_PASSED): SystemState.IDLE,
    (SystemState.IDLE, EventType.START_SIMULACRO): SystemState.SIMULACRO_ACTIVE,
    (SystemState.SIMULACRO_ACTIVE, EventType.STOP_REQUESTED): SystemState.STOPPED,
}


def transition(state: SystemState, event: EventType) -> StateTransition:
    """Return the next state without performing any side effects."""
    try:
        resulting_state = _TRANSITIONS[(state, event)]
    except KeyError as error:
        raise InvalidTransition(state, event) from error
    return StateTransition(
        event=event,
        previous_state=state,
        resulting_state=resulting_state,
    )
