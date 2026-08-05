from __future__ import annotations

from datetime import UTC, datetime

import pytest

from asm.application.controller import SystemController
from asm.domain.states import EventType, SystemState
from asm.domain.transitions import InvalidTransition
from asm.infrastructure.fakes import FakeClock, InMemoryDisplay, InMemoryEventLog


def _controller() -> tuple[SystemController, InMemoryDisplay, InMemoryEventLog]:
    display = InMemoryDisplay()
    event_log = InMemoryEventLog()
    controller = SystemController(
        clock=FakeClock(datetime(2026, 8, 5, tzinfo=UTC)),
        display=display,
        event_log=event_log,
    )
    return controller, display, event_log


def test_complete_initial_flow_is_rendered_and_audited() -> None:
    controller, display, event_log = _controller()
    controller.present()

    for event in (
        EventType.BOOT_COMPLETED,
        EventType.SELF_TEST_PASSED,
        EventType.START_SIMULACRO,
        EventType.STOP_REQUESTED,
    ):
        controller.dispatch(event)

    assert controller.state is SystemState.STOPPED
    assert [view.state for view in display.history] == [
        SystemState.BOOT,
        SystemState.SELF_TEST,
        SystemState.IDLE,
        SystemState.SIMULACRO_ACTIVE,
        SystemState.STOPPED,
    ]
    assert len(event_log.records) == 4
    assert all(record.accepted for record in event_log.records)


def test_invalid_event_is_audited_without_changing_or_rendering() -> None:
    controller, display, event_log = _controller()

    with pytest.raises(InvalidTransition):
        controller.dispatch(EventType.START_SIMULACRO)

    assert controller.state is SystemState.BOOT
    assert display.history == []
    assert len(event_log.records) == 1
    assert event_log.records[0].accepted is False
    assert event_log.records[0].resulting_state is None
