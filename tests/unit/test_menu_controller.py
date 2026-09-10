from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from asm.application.menu_controller import (
    DEFAULT_MENU,
    MenuAction,
    MenuActionKind,
    MenuController,
)
from asm.application.menu_input import MenuCommand
from asm.application.ports import MenuView


@dataclass(slots=True)
class FakeMenuDisplay:
    history: list[MenuView] = field(default_factory=list)

    def show_menu(self, view: MenuView) -> None:
        self.history.append(view)


def _controller() -> tuple[MenuController, FakeMenuDisplay]:
    display = FakeMenuDisplay()
    return MenuController(display=display, root=DEFAULT_MENU), display


def test_open_renders_root_with_first_item_selected() -> None:
    menu, display = _controller()

    view = menu.open()

    assert view.title == "Menu principal"
    assert view.items == ("Recepcion", "Audio", "Diagnostico", "Sistema", "Informacion")
    assert view.selected_index == 0
    assert display.history == [view]


def test_vertical_navigation_wraps_in_both_directions() -> None:
    menu, _display = _controller()
    menu.open()

    menu.handle(MenuCommand.MOVE_UP)

    assert menu.current_view is not None
    assert menu.current_view.selected_index == 4
    menu.handle(MenuCommand.MOVE_DOWN)
    assert menu.current_view.selected_index == 0


def test_confirm_enters_child_and_back_restores_parent_cursor() -> None:
    menu, _display = _controller()
    menu.open()
    menu.handle(MenuCommand.MOVE_DOWN)

    assert menu.handle(MenuCommand.CONFIRM) is None
    assert menu.current_view is not None
    assert menu.current_view.title == "Audio"

    assert menu.handle(MenuCommand.GO_BACK) is None
    assert menu.current_view is not None
    assert menu.current_view.title == "Menu principal"
    assert menu.current_view.selected_index == 1


def test_right_selects_leaf_as_application_action() -> None:
    menu, _display = _controller()
    menu.open()
    menu.handle(MenuCommand.CONFIRM)

    assert menu.handle(MenuCommand.MOVE_RIGHT) == MenuAction(
        MenuActionKind.SELECT,
        "receiver.channel",
    )


def test_back_at_root_closes_menu() -> None:
    menu, _display = _controller()
    menu.open()

    assert menu.handle(MenuCommand.MOVE_LEFT) is None
    assert menu.is_open is False
    assert menu.current_view is None


def test_listen_is_global_even_when_menu_is_closed() -> None:
    menu, _display = _controller()

    assert menu.handle(MenuCommand.TOGGLE_LISTEN) == MenuAction(
        MenuActionKind.TOGGLE_LISTEN
    )


def test_closed_menu_ignores_navigation() -> None:
    menu, display = _controller()

    assert menu.handle(MenuCommand.MOVE_DOWN) is None
    assert display.history == []


def test_refresh_renders_current_page_after_temporary_view() -> None:
    menu, display = _controller()
    menu.open()
    menu.handle(MenuCommand.CONFIRM)

    view = menu.refresh()

    assert view.title == "Recepcion"
    assert display.history[-1] == view


def test_refresh_rejects_closed_menu() -> None:
    menu, _display = _controller()

    with pytest.raises(RuntimeError, match="closed menu"):
        menu.refresh()
