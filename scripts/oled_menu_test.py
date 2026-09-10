"""Exercise the real OLED menu with the seven PCF8574 carrier buttons."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence

from asm.application.menu_controller import DEFAULT_MENU, MenuController
from asm.application.menu_input import MenuCommand
from asm.application.ports import SystemView
from asm.config import DEFAULT_CONFIG
from asm.domain.states import SystemState
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.i2c.pcf8574_menu_buttons import Pcf8574MenuButtons


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=180.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Render and navigate the menu without applying hardware settings."""
    args = _parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    display = LumaOledDisplay.open(branding=DEFAULT_CONFIG.branding)
    menu = MenuController(display=display, root=DEFAULT_MENU)
    idle = SystemView(
        state=SystemState.IDLE,
        title="Sistema listo",
        detail="ENTER abre menu",
    )

    def command_received(command: MenuCommand) -> None:
        if not menu.is_open and command is MenuCommand.CONFIRM:
            menu.open()
            print("MENU opened")
            return

        action = menu.handle(command)
        print(f"COMMAND {command}")
        if action is not None:
            print(f"ACTION {action.kind} target={action.target or '-'}")
        if not menu.is_open:
            display.show(idle)
            print("MENU closed; press Enter to reopen")

    panel = Pcf8574MenuButtons.open(
        on_command=command_received,
        debounce_seconds=DEFAULT_CONFIG.menu_buttons.debounce_seconds,
    )
    menu.open()
    print("READY menu shown on OLED; settings are read-only in this diagnostic")
    print("Use directions, Enter, Back, and Listen")
    try:
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            panel.poll()
            time.sleep(0.01)
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        panel.close()
        display.clear()


if __name__ == "__main__":
    raise SystemExit(main())
