"""Show the application's real BOOT view on the carrier OLED."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence

from asm.application.controller import SystemController
from asm.infrastructure.console import JsonLineEventLog, SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Render BOOT through SystemController, wait, and clear the hardware."""
    args = _parser().parse_args(argv)
    if args.seconds <= 0:
        raise SystemExit("--seconds must be greater than zero")

    display = LumaOledDisplay.open()
    controller = SystemController(
        clock=SystemClock(),
        display=display,
        event_log=JsonLineEventLog(stream=sys.stdout),
    )

    # This is intentionally the only application action in this increment.
    # No synthetic event or automatic state transition is introduced here.
    controller.present()
    try:
        time.sleep(args.seconds)
    finally:
        display.clear()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
