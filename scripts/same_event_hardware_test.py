"""Inject one bounded SAME event through the production hardware outputs."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from contextlib import ExitStack
from pathlib import Path

from asm.application.event_audio import EventAudioService
from asm.application.same_indicator_supervisor import (
    SameIndicatorSupervisor,
    SameLineOutcome,
)
from asm.application.same_message_service import SameMessageService
from asm.config import DEFAULT_CONFIG
from asm.domain.same import SameEventCode
from asm.infrastructure.audio.alsa_player import AlsaAudioPlayer
from asm.infrastructure.console import SystemClock
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.gpio.indicator_panel import GpioIndicatorPanel
from asm.infrastructure.storage.diagnostic_log import JsonLineDiagnosticLog
from asm.infrastructure.storage.same_notice_history import JsonLineSameNoticeRepository

_RELEASE_ROOT = Path(__file__).resolve().parents[1]
_TEST_HEADERS = {
    SameEventCode.RWT: "EAS: ZCZC-CIV-RWT-000000+0300-TEST0001-TEST/001-",
    SameEventCode.EQW: "EAS: ZCZC-CIV-EQW-000000+0001-TEST0001-TEST/001-",
}


def _bounded_seconds(value: str) -> float:
    seconds = float(value)
    if not 1 <= seconds <= 60:
        raise argparse.ArgumentTypeError("seconds must be between 1 and 60")
    return seconds


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event",
        choices=tuple(event.value for event in SameEventCode),
        default=SameEventCode.EQW.value,
    )
    parser.add_argument("--seconds", type=_bounded_seconds, default=15.0)
    parser.add_argument(
        "--audio-directory",
        type=Path,
        default=_RELEASE_ROOT / "assets/audio",
    )
    parser.add_argument(
        "--playback-device",
        default="plughw:CARD=Headphones,DEV=0",
    )
    parser.add_argument(
        "--oled-controller",
        choices=("sh1106", "ssd1306"),
        default="sh1106",
    )
    parser.add_argument(
        "--diagnostic-log",
        type=Path,
        default=Path("/tmp/asm-same-hardware-test.jsonl"),
        help="Separate test log; never defaults to the operational audit log",
    )
    parser.add_argument(
        "--notice-history",
        type=Path,
        default=Path("/tmp/asm-same-hardware-test-notices.jsonl"),
        help="Separate test history; never defaults to operational state",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    event = SameEventCode(args.event)
    header = _TEST_HEADERS[event]
    clock = SystemClock()
    log = JsonLineDiagnosticLog(args.diagnostic_log)

    print(f"TEST event={event.value} duration={args.seconds:g}s header={header}", flush=True)
    with ExitStack() as resources:
        display = LumaOledDisplay.open(
            branding=DEFAULT_CONFIG.branding,
            controller=args.oled_controller,
        )
        resources.callback(display.standby)
        panel = GpioIndicatorPanel.open()
        resources.callback(panel.close)
        audio = EventAudioService(
            player=AlsaAudioPlayer.open_device(args.playback_device),
            asset_directory=args.audio_directory,
            clock=clock,
            diagnostic_log=log,
        )
        resources.callback(audio.close)
        messages = SameMessageService(
            indicators=SameIndicatorSupervisor(
                indicators=panel,
                monotonic=time.monotonic,
            ),
            clock=clock,
            display=display,
            audio=audio,
            diagnostic_log=log,
            notice_history=JsonLineSameNoticeRepository(args.notice_history),
            monotonic=time.monotonic,
            rwt_notice_seconds=DEFAULT_CONFIG.display.rwt_notice_seconds,
            rwt_summary_seconds=DEFAULT_CONFIG.display.rwt_summary_seconds,
            standby_after_rwt=True,
        )

        outcome = messages.consume(header)
        if outcome is not SameLineOutcome.ACCEPTED:
            raise RuntimeError(f"test header was not accepted: {outcome.value}")
        if not messages.flush_display():
            raise RuntimeError("test event could not be rendered on the OLED")

        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            messages.poll()
            if messages.display_update_pending:
                messages.flush_display()
            time.sleep(0.05)

    print(f"PASS {event.value} audio/LED/OLED hardware path completed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
