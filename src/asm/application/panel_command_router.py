"""Map physical panel intentions onto auditable domain events."""

from __future__ import annotations

from typing import Protocol

from asm.application.button_policy import ButtonCommand
from asm.domain.models import StateTransition
from asm.domain.states import EventSource, EventType

BUTTON_EVENTS: dict[ButtonCommand, EventType] = {
    ButtonCommand.START_SIMULACRO: EventType.START_SIMULACRO,
    ButtonCommand.START_EVACUACION: EventType.START_EVACUACION,
    ButtonCommand.STOP: EventType.STOP_REQUESTED,
}


class EventDispatcher(Protocol):
    """Narrow SystemController surface used by the local panel."""

    def dispatch(
        self,
        event: EventType,
        *,
        source: EventSource = EventSource.SYSTEM,
    ) -> StateTransition: ...


class PanelCommandRouter:
    """Preserve local-panel provenance while reusing the state machine."""

    def __init__(self, dispatcher: EventDispatcher) -> None:
        self._dispatcher = dispatcher

    def handle(self, command: ButtonCommand) -> StateTransition:
        return self._dispatcher.dispatch(
            BUTTON_EVENTS[command],
            source=EventSource.LOCAL_PANEL,
        )
