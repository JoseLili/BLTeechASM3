"""Run the direct operator buttons with OLED, LEDs, power supervision, and logs."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from contextlib import ExitStack
from pathlib import Path
from queue import Empty, SimpleQueue

from asm.application.button_policy import ButtonCommand
from asm.application.controller import SystemController
from asm.application.panel_command_router import PanelCommandRouter
from asm.application.power_supervisor import PowerSupervisor
from asm.config import DEFAULT_CONFIG
from asm.domain.states import EventType
from asm.domain.transitions import InvalidTransition
from asm.infrastructure.console import SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.gpio.button_panel import GpioButtonPanel
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel
from asm.infrastructure.gpio.power_monitor import GpioPowerMonitor
from asm.infrastructure.storage.audit_log import JsonLineAuditLog
from asm.infrastructure.storage.diagnostic_log import JsonLineDiagnosticLog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument(
        "--audit-log",
        type=Path,
        default=Path.home() / ".local/state/asm-blteech/demo-audit.jsonl",
    )
    parser.add_argument(
        "--diagnostic-log",
        type=Path,
        default=Path.home() / ".local/state/asm-blteech/diagnostics.jsonl",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Serialize GPIO callbacks through one deterministic application loop."""
    args = _parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    commands: SimpleQueue[ButtonCommand] = SimpleQueue()
    with ExitStack() as resources:
        display = LumaOledDisplay.open(branding=DEFAULT_CONFIG.branding)
        resources.callback(display.clear)
        indicators = GpioIndicatorPanel.open()
        resources.callback(indicators.close)
        power_monitor = GpioPowerMonitor.open()
        resources.callback(power_monitor.close)

        controller = SystemController(
            clock=SystemClock(),
            display=display,
            event_log=JsonLineAuditLog(args.audit_log),
            indicators=indicators,
        )
        router = PanelCommandRouter(controller)
        power_supervisor = PowerSupervisor(
            monitor=power_monitor,
            clock=SystemClock(),
            monotonic=time.monotonic,
            display=display,
            diagnostic_log=JsonLineDiagnosticLog(args.diagnostic_log),
            debounce_seconds=DEFAULT_CONFIG.power_monitoring.debounce_seconds,
        )
        panel = GpioButtonPanel.open(
            config=DEFAULT_CONFIG.buttons,
            monotonic=time.monotonic,
            on_command=commands.put,
        )
        resources.callback(panel.close)

        # This executable is explicitly a hardware demo, not the production
        # self-test implementation. Its separate log path prevents confusion.
        controller.present()
        controller.dispatch(EventType.BOOT_COMPLETED)
        controller.dispatch(EventType.SELF_TEST_PASSED)
        power_supervisor.poll()
        print("READY demo: Simulacro, Evacuacion and Paro are active")
        print(f"AUDIT {args.audit_log}")
        print(f"POWER {args.diagnostic_log}")

        try:
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                panel.poll()
                while True:
                    try:
                        command = commands.get_nowait()
                    except Empty:
                        break
                    try:
                        result = router.handle(command)
                    except InvalidTransition as error:
                        print(f"REJECTED {command.value}: {error}")
                    else:
                        print(
                            f"ACCEPTED {command.value}: "
                            f"{result.previous_state.value}->{result.resulting_state.value}"
                        )
                for record in power_supervisor.poll():
                    print(f"POWER_EVENT {record.code}")
                time.sleep(0.01)
            return 0
        except KeyboardInterrupt:
            return 130


if __name__ == "__main__":
    raise SystemExit(main())
