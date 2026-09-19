"""Run a one-hot lamp test over all four Carrier Rev A indicators."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence

from asm.domain.indicators import Indicator, IndicatorState
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=1.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Light each output alone and guarantee all outputs off at exit."""
    args = _parser().parse_args(argv)
    if args.seconds <= 0:
        raise SystemExit("--seconds must be greater than zero")

    panel = GpioIndicatorPanel.open()
    try:
        for indicator in Indicator:
            print(f"ON {indicator.value}")
            panel.apply(IndicatorState.only(indicator))
            time.sleep(args.seconds)
        print("OFF ALL")
        panel.apply(IndicatorState())
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        panel.close()


if __name__ == "__main__":
    raise SystemExit(main())
