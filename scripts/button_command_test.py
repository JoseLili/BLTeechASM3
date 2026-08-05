"""Print one semantic command from every physical carrier button."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from threading import Event

from asm.application.button_policy import ButtonCommand
from asm.config import DEFAULT_CONFIG
from asm.infrastructure.gpio.button_panel import GpioButtonPanel


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the adapter and stop after all three distinct commands arrive."""
    args = _parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    completed = Event()
    observed: set[ButtonCommand] = set()

    def command_received(command: ButtonCommand) -> None:
        observed.add(command)
        print(f"COMMAND {command} completed={len(observed)}/3")
        if len(observed) == 3:
            completed.set()

    panel = GpioButtonPanel.open(
        config=DEFAULT_CONFIG.buttons,
        monotonic=time.monotonic,
        on_command=command_received,
    )
    print("READY press Simulacro, Paro, and Evacuacion once in any order")
    try:
        deadline = time.monotonic() + args.timeout
        while not completed.is_set() and time.monotonic() < deadline:
            panel.poll()
            completed.wait(0.01)
        if not completed.is_set():
            missing = sorted(command for command in ButtonCommand if command not in observed)
            print(f"TIMEOUT missing={','.join(missing)}")
            return 2
        print("PASS physical panel produced all semantic commands")
        return 0
    finally:
        panel.close()


if __name__ == "__main__":
    raise SystemExit(main())
