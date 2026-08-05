"""Show the application's real BOOT view on the carrier OLED."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence

from asm.application.controller import SystemController
from asm.infrastructure.console import JsonLineEventLog, SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.display.startup_animation import StartupAnimator


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

    # Branding is restricted to startup. Event views always bypass the animator.
    StartupAnimator(display=display, sleep=time.sleep).play()

    # No synthetic event or automatic state transition is introduced here: the
    # stable image comes from the controller's real BOOT state.
    controller.present()
    try:
        time.sleep(args.seconds)
    finally:
        display.clear()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
