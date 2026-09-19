"""Run the first hardware-free ASM BLTeech state-flow demonstration."""

from __future__ import annotations

import sys

from asm.application.controller import SystemController
from asm.domain.states import EventType
from asm.infrastructure.console import (
    ConsoleDisplay,
    ConsoleIndicatorPanel,
    JsonLineEventLog,
    SystemClock,
)


def main() -> None:
    controller = SystemController(
        clock=SystemClock(),
        display=ConsoleDisplay(sys.stdout),
        event_log=JsonLineEventLog(sys.stdout),
        indicators=ConsoleIndicatorPanel(sys.stdout),
    )
    controller.present()
    for event in (
        EventType.BOOT_COMPLETED,
        EventType.SELF_TEST_PASSED,
        EventType.START_SIMULACRO,
        EventType.STOP_REQUESTED,
    ):
        controller.dispatch(event)


if __name__ == "__main__":
    main()
