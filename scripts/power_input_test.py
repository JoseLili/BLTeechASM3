"""Observe all five Carrier Rev A power-status inputs without applying rules."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence

from asm.domain.power import PowerSignal, PowerStatus
from asm.infrastructure.gpio.power_monitor import GpioPowerMonitor


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--interval", type=float, default=0.05)
    return parser


def _describe(status: PowerStatus) -> str:
    return " ".join(
        f"{signal.value}={status.state_for(signal).value}" for signal in PowerSignal
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Print the initial snapshot and every subsequent electrical transition."""
    args = _parser().parse_args(argv)
    if args.duration <= 0 or args.interval <= 0:
        raise SystemExit("--duration and --interval must be greater than zero")

    monitor = GpioPowerMonitor.open()
    previous: PowerStatus | None = None
    try:
        deadline = time.monotonic() + args.duration
        print("READY observing GPIO5, GPIO13, GPIO26, GPIO6, and GPIO12")
        while time.monotonic() < deadline:
            current = monitor.read()
            if current != previous:
                print(f"STATUS {_describe(current)}")
                previous = current
            time.sleep(args.interval)
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        monitor.close()


if __name__ == "__main__":
    raise SystemExit(main())
