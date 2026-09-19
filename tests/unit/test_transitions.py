from __future__ import annotations

import pytest

from asm.domain.states import EventType, SystemState
from asm.domain.transitions import InvalidTransition, transition


@pytest.mark.parametrize(
    ("initial", "event", "expected"),
    [
        (SystemState.BOOT, EventType.BOOT_COMPLETED, SystemState.SELF_TEST),
        (SystemState.SELF_TEST, EventType.SELF_TEST_PASSED, SystemState.IDLE),
        (SystemState.IDLE, EventType.START_RWT, SystemState.RWT_ACTIVE),
        (SystemState.IDLE, EventType.START_SIMULACRO, SystemState.SIMULACRO_ACTIVE),
        (
            SystemState.IDLE,
            EventType.START_EVACUACION,
            SystemState.EVACUACION_ACTIVE,
        ),
        (SystemState.IDLE, EventType.START_EQW, SystemState.EQW_ACTIVE),
        (
            SystemState.RWT_ACTIVE,
            EventType.START_SIMULACRO,
            SystemState.SIMULACRO_ACTIVE,
        ),
        (
            SystemState.SIMULACRO_ACTIVE,
            EventType.START_EVACUACION,
            SystemState.EVACUACION_ACTIVE,
        ),
        (
            SystemState.EVACUACION_ACTIVE,
            EventType.START_EQW,
            SystemState.EQW_ACTIVE,
        ),
        (SystemState.TECH_MODE, EventType.START_EQW, SystemState.EQW_ACTIVE),
        (
            SystemState.SIMULACRO_ACTIVE,
            EventType.STOP_REQUESTED,
            SystemState.STOPPED,
        ),
        (
            SystemState.EVACUACION_ACTIVE,
            EventType.STOP_REQUESTED,
            SystemState.STOPPED,
        ),
        (SystemState.RWT_ACTIVE, EventType.STOP_REQUESTED, SystemState.STOPPED),
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


@pytest.mark.parametrize(
    ("initial", "event"),
    [
        (SystemState.SIMULACRO_ACTIVE, EventType.START_RWT),
        (SystemState.EVACUACION_ACTIVE, EventType.START_SIMULACRO),
        (SystemState.EQW_ACTIVE, EventType.START_EVACUACION),
        (SystemState.EQW_ACTIVE, EventType.STOP_REQUESTED),
        (SystemState.IDLE, EventType.STOP_REQUESTED),
        (SystemState.TECH_MODE, EventType.START_EVACUACION),
    ],
)
def test_lower_equal_or_unauthorized_events_are_rejected(
    initial: SystemState,
    event: EventType,
) -> None:
    with pytest.raises(InvalidTransition):
        transition(initial, event)
