"""Semantic commands produced by the dedicated configuration keypad.

The application names operator intent here. PCF8574 bits, active-low levels,
I2C addresses, and GPIO interrupts remain infrastructure details.
"""

from __future__ import annotations

from enum import StrEnum


class MenuButton(StrEnum):
    """Physical labels printed on the carrier's configuration keypad."""

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    ENTER = "ENTER"
    BACK = "BACK"
    LISTEN = "LISTEN"


class MenuCommand(StrEnum):
    """Technology-neutral intent consumed by the future menu controller."""

    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    CONFIRM = "CONFIRM"
    GO_BACK = "GO_BACK"
    TOGGLE_LISTEN = "TOGGLE_LISTEN"


_COMMANDS: dict[MenuButton, MenuCommand] = {
    MenuButton.UP: MenuCommand.MOVE_UP,
    MenuButton.DOWN: MenuCommand.MOVE_DOWN,
    MenuButton.LEFT: MenuCommand.MOVE_LEFT,
    MenuButton.RIGHT: MenuCommand.MOVE_RIGHT,
    MenuButton.ENTER: MenuCommand.CONFIRM,
    MenuButton.BACK: MenuCommand.GO_BACK,
    MenuButton.LISTEN: MenuCommand.TOGGLE_LISTEN,
}


def command_for_menu_button(button: MenuButton) -> MenuCommand:
    """Translate one validated keypad button into application intent."""
    return _COMMANDS[button]
