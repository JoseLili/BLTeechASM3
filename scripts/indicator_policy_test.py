"""Show the system-state indicator policy on the physical Carrier Rev A panel."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence

from asm.application.indicator_policy import indicator_state_for
from asm.domain.indicators import Indicator
from asm.domain.states import SystemState
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel

_DEMO_STATES = (
    SystemState.IDLE,
    SystemState.RWT_ACTIVE,
    SystemState.SIMULACRO_ACTIVE,
    SystemState.EVACUACION_ACTIVE,
    SystemState.EQW_ACTIVE,
    SystemState.POWER_FAULT,
    SystemState.STOPPED,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=1.5)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.seconds <= 0:
        raise SystemExit("--seconds must be greater than zero")

    panel = GpioIndicatorPanel.open()
    try:
        for state in _DEMO_STATES:
            indicator_state = indicator_state_for(state)
            active = [item.value for item in Indicator if indicator_state.is_on(item)]
            print(f"STATE {state.value} LEDS={','.join(active)}")
            panel.apply(indicator_state)
            time.sleep(args.seconds)
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        panel.close()
        print("OFF ALL")


if __name__ == "__main__":
    raise SystemExit(main())
