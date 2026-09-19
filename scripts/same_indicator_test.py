"""Blink the real Advisory or Warning LED from a representative SAME header."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence

from asm.application.same_indicator_supervisor import SameIndicatorSupervisor
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel

_HEADERS = {
    "RWT": "EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-",
    "EQW": "EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=tuple(_HEADERS))
    parser.add_argument("--seconds", type=float, default=6.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not 0 < args.seconds <= 30:
        raise SystemExit("--seconds must be greater than zero and at most 30")

    with GpioIndicatorPanel.open() as panel:
        supervisor = SameIndicatorSupervisor(
            indicators=panel,
            monotonic=time.monotonic,
        )
        outcome = supervisor.handle_line(_HEADERS[args.event])
        print(f"{outcome} {args.event}; bounded HIL window={args.seconds}s")
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            supervisor.poll()
            time.sleep(0.05)

    print("PASS bounded blink test completed and all indicators are off")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
