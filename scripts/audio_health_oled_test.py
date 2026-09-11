"""Show WM8960 readiness on the physical OLED for a bounded interval."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence

from asm.application.audio_presenter import audio_status_view
from asm.config import DEFAULT_CONFIG
from asm.infrastructure.audio.alsa_health import AlsaAudioHealth
from asm.infrastructure.display.luma_oled import LumaOledDisplay


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=5.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not 0 < args.seconds <= 30:
        raise SystemExit("--seconds must be greater than zero and at most 30")

    status = AlsaAudioHealth.open(DEFAULT_CONFIG.audio).read()
    display = LumaOledDisplay.open(branding=DEFAULT_CONFIG.branding)
    try:
        display.show_menu(audio_status_view(status))
        time.sleep(args.seconds)
    finally:
        display.clear()

    if status.ready_for_capture and status.ready_for_playback:
        print("PASS WM8960 readiness rendered on OLED")
        return 0
    print("FAIL WM8960 is not ready")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
