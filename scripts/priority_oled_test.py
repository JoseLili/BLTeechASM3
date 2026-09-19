"""Show the complete operational priority sequence on the physical OLED and LEDs."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence
from contextlib import ExitStack

from asm.application.controller import SystemController
from asm.config import DEFAULT_CONFIG
from asm.domain.states import EventSource, EventType
from asm.infrastructure.console import JsonLineEventLog, SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel

_EVENTS = (
    EventType.BOOT_COMPLETED,
    EventType.SELF_TEST_PASSED,
    EventType.START_RWT,
    EventType.START_SIMULACRO,
    EventType.START_EVACUACION,
    EventType.START_EQW,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=1.5)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.seconds <= 0:
        raise SystemExit("--seconds must be greater than zero")

    with ExitStack() as resources:
        display = LumaOledDisplay.open(branding=DEFAULT_CONFIG.branding)
        resources.callback(display.clear)
        indicators = GpioIndicatorPanel.open()
        resources.callback(indicators.close)
        controller = SystemController(
            clock=SystemClock(),
            display=display,
            event_log=JsonLineEventLog(sys.stdout),
            indicators=indicators,
        )
        controller.present()
        print("STATE BOOT")
        time.sleep(args.seconds)
        try:
            for event in _EVENTS:
                result = controller.dispatch(event, source=EventSource.SYSTEM)
                print(f"STATE {result.resulting_state.value}")
                time.sleep(args.seconds)
            return 0
        except KeyboardInterrupt:
            return 130


if __name__ == "__main__":
    raise SystemExit(main())
