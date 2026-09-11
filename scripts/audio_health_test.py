"""Report WM8960 ALSA enumeration and preload readiness."""

from __future__ import annotations

from asm.application.audio_presenter import audio_status_view
from asm.config import DEFAULT_CONFIG
from asm.infrastructure.audio.alsa_health import AlsaAudioHealth


def main() -> int:
    status = AlsaAudioHealth.open(DEFAULT_CONFIG.audio).read()
    for line in audio_status_view(status).items:
        print(line)
    if status.ready_for_capture and status.ready_for_playback:
        print("PASS WM8960 is ready for capture and playback")
        return 0
    print("FAIL WM8960 is not ready")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
