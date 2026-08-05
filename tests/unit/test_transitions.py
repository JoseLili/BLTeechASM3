from __future__ import annotations

import pytest

from asm.domain.states import EventType, SystemState
from asm.domain.transitions import InvalidTransition, transition


@pytest.mark.parametrize(
    ("initial", "event", "expected"),
    [
        (SystemState.BOOT, EventType.BOOT_COMPLETED, SystemState.SELF_TEST),
        (SystemState.SELF_TEST, EventType.SELF_TEST_PASSED, SystemState.IDLE),
        (SystemState.IDLE, EventType.START_SIMULACRO, SystemState.SIMULACRO_ACTIVE),
        (
            SystemState.SIMULACRO_ACTIVE,
            EventType.STOP_REQUESTED,
            SystemState.STOPPED,
        ),
    ],
)
def test_valid_transition(
    initial: SystemState,
    event: EventType,
    expected: SystemState,
) -> None:
    result = transition(initial, event)

    assert result.previous_state is initial
    assert result.event is event
    assert result.resulting_state is expected


def test_invalid_transition_preserves_context() -> None:
    with pytest.raises(InvalidTransition) as captured:
        transition(SystemState.BOOT, EventType.START_SIMULACRO)

    assert captured.value.state is SystemState.BOOT
    assert captured.value.event is EventType.START_SIMULACRO
