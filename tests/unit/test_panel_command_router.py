from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from asm.application.button_policy import ButtonCommand
from asm.application.panel_command_router import PanelCommandRouter
from asm.domain.models import StateTransition
from asm.domain.states import EventSource, EventType, SystemState


@dataclass
class FakeDispatcher:
    calls: list[tuple[EventType, EventSource]] = field(default_factory=list)

    def dispatch(
        self,
        event: EventType,
        *,
        source: EventSource = EventSource.SYSTEM,
    ) -> StateTransition:
        self.calls.append((event, source))
        return StateTransition(event, SystemState.IDLE, SystemState.STOPPED)


@pytest.mark.parametrize(
    ("command", "event"),
    [
        (ButtonCommand.START_SIMULACRO, EventType.START_SIMULACRO),
        (ButtonCommand.START_EVACUACION, EventType.START_EVACUACION),
        (ButtonCommand.STOP, EventType.STOP_REQUESTED),
    ],
)
def test_panel_command_preserves_local_origin(
    command: ButtonCommand,
    event: EventType,
) -> None:
    dispatcher = FakeDispatcher()
    router = PanelCommandRouter(dispatcher)

    result = router.handle(command)

    assert result.event is event
    assert dispatcher.calls == [(event, EventSource.LOCAL_PANEL)]
