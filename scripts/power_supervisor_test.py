"""Observe debounced Mean Well changes, notify, and persist their JSONL evidence."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from asm.application.ports import DiagnosticDisplayPort
from asm.application.power_supervisor import PowerSupervisor
from asm.config import DEFAULT_CONFIG
from asm.infrastructure.console import ConsoleDisplay, SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.gpio.power_monitor import GpioPowerMonitor
from asm.infrastructure.storage.diagnostic_log import JsonLineDiagnosticLog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--console", action="store_true", help="Do not open the OLED")
    parser.add_argument(
        "--log-path",
        type=Path,
        default=Path.home() / ".local/state/asm-blteech/diagnostics.jsonl",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    oled: LumaOledDisplay | None = None
    if args.console:
        display: DiagnosticDisplayPort = ConsoleDisplay(sys.stdout)
    else:
        oled = LumaOledDisplay.open(branding=DEFAULT_CONFIG.branding)
        display = oled

    try:
        monitor = GpioPowerMonitor.open()
    except RuntimeError:
        if oled is not None:
            oled.clear()
        raise

    supervisor = PowerSupervisor(
        monitor=monitor,
        clock=SystemClock(),
        monotonic=time.monotonic,
        display=display,
        diagnostic_log=JsonLineDiagnosticLog(args.log_path),
        debounce_seconds=DEFAULT_CONFIG.power_monitoring.debounce_seconds,
    )
    supervisor.poll()
    print(f"READY debounce=250ms log={args.log_path}")
    try:
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            for record in supervisor.poll():
                print(f"LOGGED {record.code} {record.message}")
            time.sleep(0.01)
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        monitor.close()
        if oled is not None:
            oled.clear()


if __name__ == "__main__":
    raise SystemExit(main())
