"""Run the first production receiver slice continuously under systemd."""

from __future__ import annotations

import argparse
import signal
import time
from collections.abc import Sequence
from contextlib import ExitStack
from pathlib import Path

from asm.application.decoder_supervisor import DecoderServiceState, DecoderSupervisor
from asm.application.ports import SystemView
from asm.application.receiver_service import ReceiverError, ReceiverService
from asm.application.same_indicator_supervisor import SameIndicatorSupervisor
from asm.application.same_message_service import SameMessageService
from asm.config import DEFAULT_CONFIG
from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity
from asm.domain.indicators import IndicatorState
from asm.domain.receiver import ReceiverProfile
from asm.domain.states import SystemState
from asm.infrastructure.audio.alsa_health import AlsaAudioHealth
from asm.infrastructure.audio.same_stream import MultimonSameStream
from asm.infrastructure.console import SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.display.startup_animation import StartupAnimator
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel
from asm.infrastructure.receiver.sa818_serial import Sa818SerialReceiver
from asm.infrastructure.rtc_health import read_rtc_status
from asm.infrastructure.storage.channel_config import JsonReceiverChannelRepository
from asm.infrastructure.storage.diagnostic_log import JsonLineDiagnosticLog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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
    args = _parser().parse_args(argv)
    clock = SystemClock()
    log = JsonLineDiagnosticLog(args.diagnostic_log)
    stop_requested = False

    def request_stop(_signal_number: int, _frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    with ExitStack() as resources:
        display = LumaOledDisplay.open(branding=DEFAULT_CONFIG.branding)
        resources.callback(display.clear)
        panel = GpioIndicatorPanel.open()
        resources.callback(panel.close)
        panel.apply(IndicatorState(power=True))

        StartupAnimator(
            display=display,
            sleep=time.sleep,
            duration_seconds=DEFAULT_CONFIG.display.startup_animation_seconds,
        ).play(cancelled=lambda: stop_requested)
        if stop_requested:
            return 0
        display.show(
            SystemView(
                state=SystemState.BOOT,
                title="ASM BLTeech",
                detail="Inicializando RX",
            )
        )

        rtc = read_rtc_status()
        _append(
            log,
            clock,
            code="RTC.READY" if rtc.present and rtc.initialized_system_clock else "RTC.DEGRADED",
            severity=(
                DiagnosticSeverity.INFO
                if rtc.present and rtc.initialized_system_clock
                else DiagnosticSeverity.WARNING
            ),
            message="RTC de respaldo inspeccionado al arrancar",
            context=(
                ("present", str(rtc.present).lower()),
                ("name", rtc.name),
                ("date", rtc.date),
                ("time_utc", rtc.time),
                ("hctosys", str(rtc.initialized_system_clock).lower()),
            ),
        )

        receiver_adapter = Sa818SerialReceiver.open(
            device=DEFAULT_CONFIG.receiver.serial_device,
            timeout_seconds=DEFAULT_CONFIG.receiver.command_timeout_seconds,
            settle_seconds=DEFAULT_CONFIG.receiver.startup_settle_seconds,
        )
        resources.callback(receiver_adapter.close)
        repository = JsonReceiverChannelRepository(args.state_file)
        channel = repository.load() or DEFAULT_CONFIG.receiver.channel
        try:
            ReceiverService(receiver_adapter).configure(ReceiverProfile.gold(channel))
        except ReceiverError as error:
            _append(
                log,
                clock,
                code="RECEIVER.STARTUP.FAILED",
                severity=DiagnosticSeverity.WARNING,
                message=str(error),
            )
            display.show(
                SystemView(
                    state=SystemState.RECEIVER_FAULT,
                    title="Falla receptor",
                    detail="Reinicio automatico",
                )
            )
            return 1
        _append(
            log,
            clock,
            code="RECEIVER.STARTUP.READY",
            severity=DiagnosticSeverity.INFO,
            message="SA818 configurado y verificado",
            context=(("channel", channel.value), ("frequency_mhz", channel.frequency_text)),
        )

        health = AlsaAudioHealth.open(DEFAULT_CONFIG.audio)
        same_indicators = SameIndicatorSupervisor(indicators=panel, monotonic=time.monotonic)
        messages = SameMessageService(
            indicators=same_indicators,
            clock=clock,
            display=display,
            diagnostic_log=log,
        )
        decoder = DecoderSupervisor(
            stream_factory=lambda: MultimonSameStream(
                config=DEFAULT_CONFIG.audio,
                health=health,
            ),
            monotonic=time.monotonic,
        )
        resources.callback(decoder.close)
        messages.present_idle()

        last_decoder_state: DecoderServiceState | None = None
        print(f"READY channel={channel.value} diagnostics={args.diagnostic_log}", flush=True)
        while not stop_requested:
            cycle = decoder.poll()
            if cycle.state is DecoderServiceState.FAILED:
                _append(
                    log,
                    clock,
                    code="DECODER.PIPELINE.FAILED",
                    severity=DiagnosticSeverity.WARNING,
                    message=cycle.error or "Falla desconocida del decoder",
                    context=(("retry_seconds", f"{cycle.retry_in_seconds:g}"),),
                )
            elif cycle.state is DecoderServiceState.STARTED:
                _append(
                    log,
                    clock,
                    code="DECODER.PIPELINE.STARTED",
                    severity=DiagnosticSeverity.INFO,
                    message="Cadena arecord/SoX/multimon-ng iniciada",
                )
            if (
                cycle.state is not last_decoder_state
                and cycle.state is not DecoderServiceState.RUNNING
            ):
                print(
                    f"DECODER state={cycle.state.value} error={cycle.error or '-'}",
                    flush=True,
                )
            last_decoder_state = cycle.state
            for line in cycle.lines:
                outcome = messages.consume(line)
                if outcome.value not in ("IGNORED",):
                    print(f"SAME outcome={outcome.value} line={line}", flush=True)
            messages.poll()
            time.sleep(0.02)

        _append(
            log,
            clock,
            code="SERVICE.STOPPED",
            severity=DiagnosticSeverity.INFO,
            message="Daemon detenido de forma ordenada",
        )
    return 0


def _append(
    log: JsonLineDiagnosticLog,
    clock: SystemClock,
    *,
    code: str,
    severity: DiagnosticSeverity,
    message: str,
    context: tuple[tuple[str, str], ...] = (),
) -> None:
    log.append(
        DiagnosticRecord(
            occurred_at=clock.now(),
            component="asm_daemon",
            code=code,
            severity=severity,
            message=message,
            context=context,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
