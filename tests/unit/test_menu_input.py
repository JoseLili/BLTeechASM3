from __future__ import annotations

import pytest

from asm.application.menu_input import MenuButton, MenuCommand, command_for_menu_button


@pytest.mark.parametrize(
    ("button", "command"),
    [
        (MenuButton.UP, MenuCommand.MOVE_UP),
        (MenuButton.DOWN, MenuCommand.MOVE_DOWN),
        (MenuButton.LEFT, MenuCommand.MOVE_LEFT),
        (MenuButton.RIGHT, MenuCommand.MOVE_RIGHT),
        (MenuButton.ENTER, MenuCommand.CONFIRM),
        (MenuButton.BACK, MenuCommand.GO_BACK),
        (MenuButton.LISTEN, MenuCommand.TOGGLE_LISTEN),
    ],
)
def test_every_menu_button_has_one_semantic_command(
    button: MenuButton,
    command: MenuCommand,
) -> None:
    assert command_for_menu_button(button) is command
