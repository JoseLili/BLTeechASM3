from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from asm.application.production_panel_controller import ProductionPanelController
from asm.domain.same import SameEventCode
from asm.domain.states import EventSource, EventType, SystemState
from asm.domain.transitions import InvalidTransition
from asm.infrastructure.fakes import FakeClock, InMemoryEventLog


@dataclass
class FakeMessages:
    active_local_event: EventType | None = None
    active_same_event: SameEventCode | None = None

    def start_local_event(self, event: EventType) -> bool:
        if self.active_same_event is SameEventCode.EQW:
            return False
        self.active_local_event = event
        return True

    def stop_local_event(self) -> bool:
        if self.active_local_event is None:
            return False
        self.active_local_event = None
        return True


def _controller(messages: FakeMessages):  # type: ignore[no-untyped-def]
    event_log = InMemoryEventLog()
    controller = ProductionPanelController(
        messages=messages,
        clock=FakeClock(datetime(2026, 9, 24, 12, 0, tzinfo=UTC)),
        event_log=event_log,
    )
    return controller, event_log


def test_simulacro_then_evacuation_then_stop_are_audited() -> None:
    messages = FakeMessages()
    controller, event_log = _controller(messages)

    first = controller.dispatch(EventType.START_SIMULACRO, source=EventSource.LOCAL_PANEL)
    second = controller.dispatch(EventType.START_EVACUACION, source=EventSource.LOCAL_PANEL)
    stopped = controller.dispatch(EventType.STOP_REQUESTED, source=EventSource.LOCAL_PANEL)

    assert first.resulting_state is SystemState.SIMULACRO_ACTIVE
    assert second.resulting_state is SystemState.EVACUACION_ACTIVE
    assert stopped.resulting_state is SystemState.STOPPED
    assert messages.active_local_event is None
    assert [record.accepted for record in event_log.records] == [True, True, True]
    assert all(record.source is EventSource.LOCAL_PANEL for record in event_log.records)


def test_eqw_blocks_local_start_and_paro_does_not_cancel_it() -> None:
    messages = FakeMessages(active_same_event=SameEventCode.EQW)
    controller, event_log = _controller(messages)

    with pytest.raises(InvalidTransition):
        controller.dispatch(EventType.START_EVACUACION, source=EventSource.LOCAL_PANEL)
    with pytest.raises(InvalidTransition):
        controller.dispatch(EventType.STOP_REQUESTED, source=EventSource.LOCAL_PANEL)

    assert messages.active_same_event is SameEventCode.EQW
    assert [record.accepted for record in event_log.records] == [False, False]


def test_rwt_remains_active_after_stopping_local_simulacro() -> None:
    messages = FakeMessages(active_same_event=SameEventCode.RWT)
    controller, _event_log = _controller(messages)

    controller.dispatch(EventType.START_SIMULACRO, source=EventSource.LOCAL_PANEL)
    controller.dispatch(EventType.STOP_REQUESTED, source=EventSource.LOCAL_PANEL)

    assert controller.state is SystemState.RWT_ACTIVE
