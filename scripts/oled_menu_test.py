"""Exercise the real OLED menu with the seven PCF8574 carrier buttons."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from pathlib import Path

from asm.application.audio_presenter import audio_status_view
from asm.application.channel_editor import (
    ChannelEditorOutcome,
    ChannelRollbackError,
    ChannelStorageError,
    ReceiverChannelEditor,
)
from asm.application.indicator_policy import indicator_state_for
from asm.application.menu_controller import DEFAULT_MENU, MenuController
from asm.application.menu_input import MenuCommand
from asm.application.ports import SystemView
from asm.application.power_presenter import power_status_view
from asm.application.power_supervisor import PowerSupervisor
from asm.application.receiver_service import ReceiverError, ReceiverService
from asm.config import DEFAULT_CONFIG
from asm.domain.receiver import ReceiverProfile
from asm.domain.states import SystemState
from asm.infrastructure.audio.alsa_health import AlsaAudioHealth
from asm.infrastructure.console import SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel
from asm.infrastructure.gpio.power_monitor import GpioPowerMonitor
from asm.infrastructure.i2c.pcf8574_menu_buttons import Pcf8574MenuButtons
from asm.infrastructure.receiver.sa818_serial import Sa818SerialReceiver
from asm.infrastructure.storage.channel_config import JsonReceiverChannelRepository
from asm.infrastructure.storage.diagnostic_log import JsonLineDiagnosticLog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path.home() / ".local/state/asm-blteech/receiver.json",
    )
    parser.add_argument(
        "--diagnostic-log",
        type=Path,
        default=Path.home() / ".local/state/asm-blteech/diagnostics.jsonl",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Navigate the menu and transactionally configure a verified channel."""
    args = _parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    repository = JsonReceiverChannelRepository(args.state_file)
    try:
        committed_channel = repository.load() or DEFAULT_CONFIG.receiver.channel
    except ChannelStorageError as error:
        print(f"FAIL {error}")
        return 2

    display = LumaOledDisplay.open(branding=DEFAULT_CONFIG.branding)
    receiver_adapter = Sa818SerialReceiver.open(
        device=DEFAULT_CONFIG.receiver.serial_device,
        timeout_seconds=DEFAULT_CONFIG.receiver.command_timeout_seconds,
        settle_seconds=DEFAULT_CONFIG.receiver.startup_settle_seconds,
    )
    receiver = ReceiverService(receiver_adapter)
    try:
        receiver.configure(ReceiverProfile.gold(committed_channel))
    except ReceiverError as error:
        receiver_adapter.close()
        display.clear()
        print(f"FAIL startup receiver configuration: {error}")
        return 2

    try:
        power_monitor = GpioPowerMonitor.open()
    except RuntimeError as error:
        receiver_adapter.close()
        display.clear()
        print(f"FAIL power monitor: {error}")
        return 2

    try:
        indicators = GpioIndicatorPanel.open()
    except RuntimeError as error:
        power_monitor.close()
        receiver_adapter.close()
        display.clear()
        print(f"FAIL indicator panel: {error}")
        return 2

    menu = MenuController(display=display, root=DEFAULT_MENU)
    channel_editor = ReceiverChannelEditor(
        display=display,
        receiver=receiver,
        repository=repository,
        committed_channel=committed_channel,
    )
    idle = SystemView(
        state=SystemState.IDLE,
        title="Sistema listo",
        detail="ENTER abre menu",
    )
    indicators.apply(indicator_state_for(SystemState.IDLE))
    audio_health = AlsaAudioHealth.open(DEFAULT_CONFIG.audio)
    power_supervisor = PowerSupervisor(
        monitor=power_monitor,
        clock=SystemClock(),
        monotonic=time.monotonic,
        display=display,
        diagnostic_log=JsonLineDiagnosticLog(args.diagnostic_log),
        debounce_seconds=DEFAULT_CONFIG.power_monitoring.debounce_seconds,
    )

    def command_received(command: MenuCommand) -> None:
        if command is MenuCommand.TOGGLE_LISTEN:
            action = menu.handle(command)
            print(f"ACTION {action.kind if action else '-'} target=-")
            return

        if channel_editor.is_open:
            try:
                outcome = channel_editor.handle(command)
            except ChannelRollbackError as error:
                print(f"CRITICAL {error}")
                return
            print(f"CHANNEL {command} outcome={outcome}")
            if outcome in (ChannelEditorOutcome.CLOSED, ChannelEditorOutcome.SAVED):
                menu.refresh()
                if outcome is ChannelEditorOutcome.SAVED:
                    print(
                        f"SAVED {channel_editor.committed_channel.value} "
                        f"{channel_editor.committed_channel.frequency_text} MHz"
                    )
            return

        if not menu.is_open and command is MenuCommand.CONFIRM:
            menu.open()
            print("MENU opened")
            return

        action = menu.handle(command)
        print(f"COMMAND {command}")
        if action is not None:
            print(f"ACTION {action.kind} target={action.target or '-'}")
            if action.target == "receiver.channel":
                channel_editor.open()
            elif action.target == "diagnostics.power":
                display.show_menu(power_status_view(power_monitor.read()))
                print("POWER diagnostic snapshot shown")
            elif action.target == "diagnostics.audio":
                display.show_menu(audio_status_view(audio_health.read()))
                print("AUDIO diagnostic snapshot shown")
        if not menu.is_open:
            display.show(idle)
            print("MENU closed; press Enter to reopen")

    panel = Pcf8574MenuButtons.open(
        on_command=command_received,
        debounce_seconds=DEFAULT_CONFIG.menu_buttons.debounce_seconds,
    )
    menu.open()
    print(
        f"READY menu shown on OLED; active channel={committed_channel.value} "
        f"state={repository.path}"
    )
    print("Channel flow: choose, Enter verifies, Enter saves; Back restores")
    try:
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            panel.poll()
            power_supervisor.poll()
            time.sleep(0.01)
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        panel.close()
        indicators.close()
        power_monitor.close()
        receiver_adapter.close()
        display.clear()


if __name__ == "__main__":
    raise SystemExit(main())
