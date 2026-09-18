"""Headless display adapter used when the physical display cannot open."""

from __future__ import annotations

from asm.application.ports import DiagnosticView, MenuView, SystemView
from asm.infrastructure.display.startup_animation import StartupFrame


class NullDisplay:
    """Accept every presentation request without touching hardware."""

    def show(self, _view: SystemView) -> None:
        return

    def show_menu(self, _view: MenuView) -> None:
        return

    def show_diagnostic(self, _view: DiagnosticView) -> None:
        return

    def show_startup_frame(self, _frame: StartupFrame) -> None:
        return

    def clear(self) -> None:
        return
