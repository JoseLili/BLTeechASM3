"""Queue menu pages through the decoder-safe OLED write path."""

from __future__ import annotations

from dataclasses import dataclass

from asm.application.ports import MenuView
from asm.application.same_message_service import SameMessageService


@dataclass(slots=True)
class SafeMenuDisplay:
    """Adapt synchronous menu presenters to the queued operational display."""

    messages: SameMessageService
    duration_seconds: float

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than zero")

    def show_menu(self, view: MenuView) -> None:
        key = ":".join(
            (
                view.title,
                str(view.selected_index),
                *view.items,
            )
        )
        self.messages.request_menu_view(
            key=key,
            view=view,
            duration_seconds=self.duration_seconds,
        )
