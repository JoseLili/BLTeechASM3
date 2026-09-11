"""Read-only readiness checks for the named WM8960 ALSA card."""

from __future__ import annotations

from typing import Self

from asm.config.models import AudioConfig
from asm.domain.audio import AudioDeviceStatus
from asm.infrastructure.audio.commands import CommandRunner, run_command


class AlsaAudioHealth:
    """Confirm preload, capture, and playback without opening PCM streams."""

    def __init__(
        self,
        *,
        card_name: str,
        preload_service: str,
        runner: CommandRunner,
    ) -> None:
        self._card_name = card_name
        self._preload_service = preload_service
        self._runner = runner

    @classmethod
    def open(cls, config: AudioConfig) -> Self:
        return cls(
            card_name=config.card_name,
            preload_service=config.preload_service,
            runner=run_command,
        )

    def read(self) -> AudioDeviceStatus:
        preload = self._runner(
            (
                "/usr/bin/systemctl",
                "show",
                self._preload_service,
                "--property=ActiveState",
                "--value",
            )
        )
        capture = self._runner(("/usr/bin/arecord", "-l"))
        playback = self._runner(("/usr/bin/aplay", "-l"))
        return AudioDeviceStatus(
            card_name=self._card_name,
            preload_ready=preload.returncode == 0 and preload.stdout.strip() == "active",
            capture_available=(
                capture.returncode == 0 and self._card_name in capture.stdout
            ),
            playback_available=(
                playback.returncode == 0 and self._card_name in playback.stdout
            ),
        )
