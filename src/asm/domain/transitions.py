"""Pure operational transition and priority rules."""

from __future__ import annotations

from asm.domain.models import StateTransition
from asm.domain.priorities import EVENT_PRIORITIES, START_EVENT_STATES, STATE_PRIORITIES
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
}

_STOPPABLE_STATES = {
    SystemState.RWT_ACTIVE,
    SystemState.SIMULACRO_ACTIVE,
    SystemState.EVACUACION_ACTIVE,
}


def transition(state: SystemState, event: EventType) -> StateTransition:
    """Return the next state without performing any side effects."""
    resulting_state = _TRANSITIONS.get((state, event))
    if (
        resulting_state is None
        and event is EventType.STOP_REQUESTED
        and state in _STOPPABLE_STATES
    ):
        resulting_state = SystemState.STOPPED
    if resulting_state is None and event in START_EVENT_STATES:
        resulting_state = _start_transition(state, event)
    if resulting_state is None:
        raise InvalidTransition(state, event)
    return StateTransition(
        event=event,
        previous_state=state,
        resulting_state=resulting_state,
    )


def _start_transition(state: SystemState, event: EventType) -> SystemState | None:
    """Accept starts from idle or preempt only a lower-priority active event."""
    target = START_EVENT_STATES[event]
    if state is SystemState.IDLE:
        return target
    if state is SystemState.TECH_MODE and event is EventType.START_EQW:
        return target
    current_priority = STATE_PRIORITIES.get(state)
    if current_priority is not None and EVENT_PRIORITIES[event] > current_priority:
        return target
    return None
