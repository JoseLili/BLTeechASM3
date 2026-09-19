"""Validate all seven dedicated PCF8574 menu buttons on the carrier."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence

from asm.application.menu_input import MenuCommand
from asm.config import DEFAULT_CONFIG
from asm.infrastructure.i2c.pcf8574_menu_buttons import Pcf8574MenuButtons


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Wait until every configuration control has produced its semantic command."""
    args = _parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    observed: set[MenuCommand] = set()

    def command_received(command: MenuCommand) -> None:
        observed.add(command)
        print(f"COMMAND {command} completed={len(observed)}/{len(MenuCommand)}")

    panel = Pcf8574MenuButtons.open(
        on_command=command_received,
        debounce_seconds=DEFAULT_CONFIG.menu_buttons.debounce_seconds,
    )
    print("READY press Arriba, Abajo, Izquierda, Derecha, Enter, Regresar, and Escucha")
    try:
        deadline = time.monotonic() + args.timeout
        while len(observed) < len(MenuCommand) and time.monotonic() < deadline:
            panel.poll()
            time.sleep(0.01)
        if len(observed) != len(MenuCommand):
            missing = sorted(command for command in MenuCommand if command not in observed)
            print(f"TIMEOUT missing={','.join(missing)}")
            return 2
        print("PASS all PCF8574 menu buttons produced semantic commands")
        return 0
    finally:
        panel.close()


if __name__ == "__main__":
    raise SystemExit(main())
