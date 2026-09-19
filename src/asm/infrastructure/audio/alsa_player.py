"""Interruptible, single-asset ALSA playback without runtime mixer writes."""

from __future__ import annotations

import signal
import subprocess
from pathlib import Path
from typing import Protocol

from asm.application.ports import AudioHealthPort
from asm.config.models import AudioConfig
from asm.infrastructure.audio.errors import (
    AudioBusyError,
    AudioProcessError,
    AudioUnavailableError,
)


class ProcessHandle(Protocol):
    def poll(self) -> int | None: ...

    def send_signal(self, signal_number: int) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def kill(self) -> None: ...


class ProcessFactory(Protocol):
    def __call__(self, arguments: tuple[str, ...]) -> ProcessHandle: ...


def _start_process(arguments: tuple[str, ...]) -> ProcessHandle:
    return subprocess.Popen(
        arguments,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class AlsaAudioPlayer:
    """Own at most one aplay process and require an explicit replacement policy."""

    def __init__(
        self,
        *,
        playback_device: str,
        process_factory: ProcessFactory,
        health: AudioHealthPort | None = None,
    ) -> None:
        if not playback_device.strip():
            raise ValueError("playback_device must not be empty")
        self._playback_device = playback_device
        self._health = health
        self._process_factory = process_factory
        self._process: ProcessHandle | None = None

    @classmethod
    def open(cls, config: AudioConfig, health: AudioHealthPort) -> AlsaAudioPlayer:
        """Open the legacy WM8960 playback route used by hardware diagnostics."""
        return cls(
            playback_device=config.pcm_device,
            health=health,
            process_factory=_start_process,
        )

    @classmethod
    def open_device(cls, playback_device: str) -> AlsaAudioPlayer:
        """Open one explicit ALSA output without coupling it to capture health."""
        return cls(playback_device=playback_device, process_factory=_start_process)

    @property
    def is_playing(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, asset: Path) -> None:
        if self.is_playing:
            raise AudioBusyError("an audio asset is already playing")
        self._process = None
        if self._health is not None and not self._health.read().ready_for_playback:
            raise AudioUnavailableError("configured ALSA playback is unavailable")
        if not asset.is_file():
            raise FileNotFoundError(asset)
        if asset.suffix.lower() != ".wav":
            raise ValueError("only WAV assets are accepted")

        process = self._process_factory(
            ("/usr/bin/aplay", "-q", "-D", self._playback_device, str(asset))
        )
        return_code = process.poll()
        if return_code not in (None, 0):
            raise AudioProcessError(f"aplay exited with status {return_code}")
        self._process = process if return_code is None else None

    def stop(self) -> None:
        process = self._process
        self._process = None
        if process is None or process.poll() is not None:
            return
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    def close(self) -> None:
        self.stop()

    def __enter__(self) -> AlsaAudioPlayer:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
