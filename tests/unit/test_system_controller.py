from __future__ import annotations

from datetime import UTC, datetime

import pytest

from asm.application.controller import SystemController
from asm.domain.states import EventSource, EventType, SystemState
from asm.domain.transitions import InvalidTransition
from asm.infrastructure.fakes import (
    FakeClock,
    InMemoryDisplay,
    InMemoryEventLog,
    InMemoryIndicatorPanel,
)


def _controller() -> tuple[
    SystemController, InMemoryDisplay, InMemoryEventLog, InMemoryIndicatorPanel
]:
    display = InMemoryDisplay()
    event_log = InMemoryEventLog()
    indicators = InMemoryIndicatorPanel()
    controller = SystemController(
        clock=FakeClock(datetime(2026, 8, 5, tzinfo=UTC)),
        display=display,
        event_log=event_log,
        indicators=indicators,
    )
    return controller, display, event_log, indicators


def test_complete_initial_flow_is_rendered_and_audited() -> None:
    controller, display, event_log, indicators = _controller()
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
    assert all(record.source is EventSource.SYSTEM for record in event_log.records)
    assert [state.power for state in indicators.history] == [True] * 5
    assert indicators.history[-2].watch is True
    assert indicators.history[-1].watch is False


def test_invalid_event_is_audited_without_changing_or_rendering() -> None:
    controller, display, event_log, indicators = _controller()

    with pytest.raises(InvalidTransition):
        controller.dispatch(EventType.START_SIMULACRO)

    assert controller.state is SystemState.BOOT
    assert display.history == []
    assert len(event_log.records) == 1
    assert event_log.records[0].accepted is False
    assert event_log.records[0].resulting_state is None
    assert indicators.history == []


def test_explicit_event_source_is_preserved() -> None:
    controller, _display, event_log, _indicators = _controller()
    controller.dispatch(EventType.BOOT_COMPLETED, source=EventSource.LOCAL_PANEL)

    assert event_log.records[0].source is EventSource.LOCAL_PANEL


def test_priority_flow_updates_oled_views_and_led_policy_together() -> None:
    controller, display, event_log, indicators = _controller()
    for event in (
        EventType.BOOT_COMPLETED,
        EventType.SELF_TEST_PASSED,
        EventType.START_RWT,
        EventType.START_SIMULACRO,
        EventType.START_EVACUACION,
        EventType.START_EQW,
    ):
        controller.dispatch(event)

    assert [view.state for view in display.history[-4:]] == [
        SystemState.RWT_ACTIVE,
        SystemState.SIMULACRO_ACTIVE,
        SystemState.EVACUACION_ACTIVE,
        SystemState.EQW_ACTIVE,
    ]
    assert indicators.history[-4].advisory is True
    assert indicators.history[-3].watch is True
    assert indicators.history[-2].watch is True
    assert indicators.history[-1].warning is True
    assert len(event_log.records) == 6


def test_event_audio_starts_before_led_and_display_outputs() -> None:
    trace: list[str] = []

    class OrderedAudio:
        def play(self, _event: EventType) -> bool:
            trace.append("audio")
            return True

        def poll(self) -> None:
            return

        def stop(self) -> None:
            trace.append("audio-stop")

    class OrderedIndicators:
        def apply(self, _state: object) -> None:
            trace.append("led")

    class OrderedDisplay:
        def show(self, _view: object) -> None:
            trace.append("display")

    controller = SystemController(
        clock=FakeClock(datetime(2026, 8, 5, tzinfo=UTC)),
        display=OrderedDisplay(),  # type: ignore[arg-type]
        event_log=InMemoryEventLog(),
        indicators=OrderedIndicators(),  # type: ignore[arg-type]
        audio=OrderedAudio(),
    )
    controller.dispatch(EventType.BOOT_COMPLETED)
    controller.dispatch(EventType.SELF_TEST_PASSED)
    trace.clear()

    controller.dispatch(EventType.START_SIMULACRO)

    assert trace == ["audio", "led", "display"]
