"""Run the first production receiver slice continuously under systemd."""

from __future__ import annotations

import argparse
import signal
import time
from collections.abc import Sequence
from contextlib import ExitStack
from datetime import UTC
from pathlib import Path

from asm.application.decoder_supervisor import DecoderServiceState, DecoderSupervisor
from asm.application.event_audio import EventAudioService
from asm.application.menu_input import MenuCommand
from asm.application.ports import SystemView
from asm.application.receiver_service import ReceiverError, ReceiverService
from asm.application.rwt_schedule_supervisor import (
    RwtScheduleState,
    RwtScheduleSupervisor,
    RwtScheduleTransition,
)
from asm.application.same_history_presenter import (
    collapse_repetitions,
    empty_history_view,
    recent_notice_view,
)
from asm.application.same_indicator_supervisor import SameIndicatorSupervisor
from asm.application.same_message_service import SameMessageService
from asm.config import DEFAULT_CONFIG
from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity
from asm.domain.indicators import IndicatorState
from asm.domain.receiver import ReceiverProfile
from asm.domain.same import SameNoticeRecord
from asm.domain.states import SystemState
from asm.infrastructure.audio.alsa_health import AlsaAudioHealth
from asm.infrastructure.audio.alsa_player import AlsaAudioPlayer
from asm.infrastructure.audio.same_stream import MultimonSameStream
from asm.infrastructure.console import SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.display.null_display import NullDisplay
from asm.infrastructure.display.startup_animation import StartupAnimator
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel
from asm.infrastructure.i2c.pcf8574_menu_buttons import Pcf8574MenuButtons
from asm.infrastructure.receiver.sa818_serial import Sa818SerialReceiver
from asm.infrastructure.rtc_health import read_rtc_status
from asm.infrastructure.storage.channel_config import JsonReceiverChannelRepository
from asm.infrastructure.storage.diagnostic_log import JsonLineDiagnosticLog
from asm.infrastructure.storage.same_notice_history import JsonLineSameNoticeRepository

_RELEASE_ROOT = Path(__file__).resolve().parents[1]


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
    parser.add_argument(
        "--notice-history",
        type=Path,
        default=Path.home() / ".local/state/asm-blteech/notices.jsonl",
        help="Historial persistente de cabeceras SAME aceptadas",
    )
    parser.add_argument(
        "--oled-controller",
        choices=("sh1106", "ssd1306"),
        default="sh1106",
        help="Controlador de la OLED 128x64 instalada",
    )
    parser.add_argument(
        "--oled-listen-mode",
        choices=("standby", "continuous"),
        default="standby",
        help="Apaga pixeles al escuchar (grande) o mantiene estado visible (pequena)",
    )
    parser.add_argument(
        "--audio-directory",
        type=Path,
        default=_RELEASE_ROOT / "assets/audio",
        help="Directorio con rwt.wav, eqw.wav, simulacro.wav y evacuacion.wav",
    )
    parser.add_argument(
        "--playback-device",
        default="plughw:CARD=Headphones,DEV=0",
        help="Dispositivo ALSA explicito para los WAV de alerta",
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
        try:
            display: LumaOledDisplay | NullDisplay = LumaOledDisplay.open(
                branding=DEFAULT_CONFIG.branding,
                controller=args.oled_controller,
            )
        except Exception as error:
            _log_display_failure(log, clock, stage="open", error=error)
            display = NullDisplay()
        resources.callback(_clear_display_safely, display, log, clock)
        panel = GpioIndicatorPanel.open()
        resources.callback(panel.close)
        panel.apply(IndicatorState(power=True))

        try:
            StartupAnimator(
                display=display,
                sleep=time.sleep,
                duration_seconds=DEFAULT_CONFIG.display.startup_animation_seconds,
            ).play(cancelled=lambda: stop_requested)
        except Exception as error:
            _log_display_failure(log, clock, stage="startup_animation", error=error)
        if stop_requested:
            return 0
        _show_safely(
            display,
            SystemView(
                state=SystemState.BOOT,
                title="ASM BLTeech",
                detail="Inicializando RX",
            ),
            log=log,
            clock=clock,
            stage="boot",
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
            _show_safely(
                display,
                SystemView(
                    state=SystemState.RECEIVER_FAULT,
                    title="Falla receptor",
                    detail="Reinicio automatico",
                ),
                log=log,
                clock=clock,
                stage="receiver_fault",
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
        alert_audio = EventAudioService(
            player=AlsaAudioPlayer.open_device(args.playback_device),
            asset_directory=args.audio_directory,
            clock=clock,
            diagnostic_log=log,
        )
        resources.callback(alert_audio.close)
        notice_history = JsonLineSameNoticeRepository(args.notice_history)
        operator_timezone = clock.now().astimezone().tzinfo or UTC
        schedule = RwtScheduleSupervisor(
            clock=clock,
            diagnostic_log=log,
            operator_timezone=operator_timezone,
        )
        schedule_transitions: list[RwtScheduleTransition] = []

        def notice_observed(record: SameNoticeRecord) -> None:
            transition = schedule.observe(record)
            if transition is not None:
                schedule_transitions.append(transition)

        same_indicators = SameIndicatorSupervisor(indicators=panel, monotonic=time.monotonic)
        messages = SameMessageService(
            indicators=same_indicators,
            clock=clock,
            display=display,
            audio=alert_audio,
            diagnostic_log=log,
            notice_history=notice_history,
            monotonic=time.monotonic,
            rwt_notice_seconds=DEFAULT_CONFIG.display.rwt_notice_seconds,
            rwt_summary_seconds=DEFAULT_CONFIG.display.rwt_summary_seconds,
            standby_after_rwt=args.oled_listen_mode == "standby",
            notice_observer=notice_observed,
        )
        try:
            recent_notices = notice_history.recent(limit=1000)
            restored = messages.restore_active(recent_notices)
            schedule.restore(recent_notices)
        except Exception as error:
            restored = 0
            _append(
                log,
                clock,
                code="SAME.HISTORY.READ.FAILED",
                severity=DiagnosticSeverity.WARNING,
                message="No fue posible restaurar el historial SAME",
                context=(
                    ("error_type", type(error).__name__),
                    ("error", str(error) or type(error).__name__),
                ),
            )
        else:
            _append(
                log,
                clock,
                code="SAME.HISTORY.RESTORED",
                severity=DiagnosticSeverity.INFO,
                message="Vigencias SAME restauradas al arrancar",
                context=(("active_notices", str(restored)),),
        )
        menu_buttons: Pcf8574MenuButtons | None = None
        history_index = 0
        history_open = False

        def apply_schedule_transition(transition: RwtScheduleTransition) -> None:
            if transition.current_status.state is RwtScheduleState.RECEIVED:
                messages.set_idle_footer("Sin RWT vigente")
                return
            expected_text = transition.expected_at.strftime("%H:%M")
            messages.set_idle_footer(f"Falta RWT {expected_text}")
            messages.request_temporary_view(
                key=f"rwt-missed:{transition.expected_at.isoformat()}",
                view=SystemView(
                    state=SystemState.RECEIVER_FAULT,
                    title="RWT NO RECIBIDO",
                    detail=f"Esperada {expected_text}",
                    footer="Revisar recepcion",
                ),
                duration_seconds=DEFAULT_CONFIG.display.idle_notice_seconds,
            )

        initial_schedule_transition = schedule.poll()

        def show_history(command: MenuCommand) -> None:
            nonlocal history_index, history_open
            try:
                records = collapse_repetitions(notice_history.recent(limit=20))
            except Exception as error:
                _append(
                    log,
                    clock,
                    code="SAME.HISTORY.READ.FAILED",
                    severity=DiagnosticSeverity.WARNING,
                    message="No fue posible consultar eventos recientes",
                    context=(
                        ("error_type", type(error).__name__),
                        ("error", str(error) or type(error).__name__),
                    ),
                )
                records = ()
            if not records:
                history_open = True
                messages.request_temporary_view(
                    key="history:empty",
                    view=empty_history_view(),
                    duration_seconds=DEFAULT_CONFIG.display.idle_notice_seconds,
                )
                return
            if not history_open:
                history_index = 0
            elif command is MenuCommand.MOVE_DOWN:
                history_index = (history_index + 1) % len(records)
            else:
                history_index = (history_index - 1) % len(records)
            history_open = True
            record = records[history_index]
            messages.request_temporary_view(
                key=f"history:{history_index}:{record.received_at.isoformat()}",
                view=recent_notice_view(
                    record,
                    index=history_index,
                    total=len(records),
                    timezone=operator_timezone,
                    now=clock.now(),
                ),
                duration_seconds=DEFAULT_CONFIG.display.idle_notice_seconds,
            )

        def menu_command_received(command: MenuCommand) -> None:
            nonlocal history_open
            if command in (MenuCommand.MOVE_DOWN, MenuCommand.MOVE_UP):
                show_history(command)
                return
            if command not in (
                MenuCommand.CONFIRM,
                MenuCommand.GO_BACK,
                MenuCommand.MOVE_LEFT,
            ):
                return
            history_open = False
            messages.request_status(
                duration_seconds=DEFAULT_CONFIG.display.idle_notice_seconds
            )
            _append(
                log,
                clock,
                code="DISPLAY.WAKE.REQUESTED",
                severity=DiagnosticSeverity.INFO,
                message="Consulta de estado solicitada con el boton Enter",
            )

        try:
            menu_buttons = Pcf8574MenuButtons.open(
                on_command=menu_command_received,
                debounce_seconds=DEFAULT_CONFIG.menu_buttons.debounce_seconds,
            )
        except Exception as error:
            _append(
                log,
                clock,
                code="MENU.INPUT.UNAVAILABLE",
                severity=DiagnosticSeverity.WARNING,
                message="Los botones de menu no estan disponibles; la recepcion continua",
                context=(
                    ("error_type", type(error).__name__),
                    ("error", str(error) or type(error).__name__),
                ),
            )
        else:
            resources.callback(menu_buttons.close)
        decoder = DecoderSupervisor(
            stream_factory=lambda: MultimonSameStream(
                config=DEFAULT_CONFIG.audio,
                health=health,
            ),
            monotonic=time.monotonic,
        )
        resources.callback(decoder.close)
        if initial_schedule_transition is None:
            messages.request_status(
                duration_seconds=DEFAULT_CONFIG.display.idle_notice_seconds
            )
        else:
            apply_schedule_transition(initial_schedule_transition)
        messages.flush_display()
        time.sleep(DEFAULT_CONFIG.display.idle_notice_seconds)
        messages.poll()
        messages.flush_display()

        last_decoder_state: DecoderServiceState | None = None
        next_schedule_poll = time.monotonic()
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
            while schedule_transitions:
                apply_schedule_transition(schedule_transitions.pop(0))
            now_monotonic = time.monotonic()
            if now_monotonic >= next_schedule_poll:
                schedule_transition = schedule.poll()
                if schedule_transition is not None:
                    apply_schedule_transition(schedule_transition)
                next_schedule_poll = now_monotonic + 1.0
            if menu_buttons is not None:
                try:
                    menu_buttons.poll()
                except Exception as error:
                    _append(
                        log,
                        clock,
                        code="MENU.INPUT.FAILED",
                        severity=DiagnosticSeverity.WARNING,
                        message="Fallo la lectura del teclado; la recepcion continua",
                        context=(
                            ("error_type", type(error).__name__),
                            ("error", str(error) or type(error).__name__),
                        ),
                    )
                    menu_buttons.close()
                    menu_buttons = None
            messages.poll()
            if messages.display_update_pending:
                _append(
                    log,
                    clock,
                    code="DISPLAY.SAFE_WINDOW.STARTED",
                    severity=DiagnosticSeverity.INFO,
                    message="Decoder pausado para actualizar pantalla por I2C",
                )
                decoder.pause()
                messages.flush_display()
                last_decoder_state = None
            time.sleep(0.02)

        _append(
            log,
            clock,
            code="SERVICE.STOPPED",
            severity=DiagnosticSeverity.INFO,
            message="Daemon detenido de forma ordenada",
        )
    return 0


def _show_safely(
    display: LumaOledDisplay | NullDisplay,
    view: SystemView,
    *,
    log: JsonLineDiagnosticLog,
    clock: SystemClock,
    stage: str,
) -> None:
    try:
        display.show(view)
    except Exception as error:
        _log_display_failure(log, clock, stage=stage, error=error)


def _clear_display_safely(
    display: LumaOledDisplay | NullDisplay,
    log: JsonLineDiagnosticLog,
    clock: SystemClock,
) -> None:
    try:
        display.clear()
    except Exception as error:
        _log_display_failure(log, clock, stage="clear", error=error)


def _log_display_failure(
    log: JsonLineDiagnosticLog,
    clock: SystemClock,
    *,
    stage: str,
    error: Exception,
) -> None:
    _append(
        log,
        clock,
        code="DISPLAY.WRITE.FAILED",
        severity=DiagnosticSeverity.WARNING,
        message="La pantalla fallo; la recepcion continua",
        context=(
            ("stage", stage),
            ("error_type", type(error).__name__),
            ("error", str(error) or type(error).__name__),
        ),
    )


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
