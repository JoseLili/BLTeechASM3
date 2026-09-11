from __future__ import annotations

import signal
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from asm.config import DEFAULT_CONFIG
from asm.domain.audio import AudioDeviceStatus
from asm.infrastructure.audio.alsa_player import AlsaAudioPlayer
from asm.infrastructure.audio.errors import AudioBusyError, AudioProcessError


@dataclass
class FakeHealth:
    ready: bool = True

    def read(self) -> AudioDeviceStatus:
        return AudioDeviceStatus(
            "wm8960soundcard",
            self.ready,
            self.ready,
            self.ready,
        )


@dataclass
class FakeProcess:
    return_code: int | None = None
    signals: list[int] = field(default_factory=list)
    wait_calls: list[float | None] = field(default_factory=list)
    kill_calls: int = 0

    def poll(self) -> int | None:
        return self.return_code

    def send_signal(self, signal_number: int) -> None:
        self.signals.append(signal_number)

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls.append(timeout)
        self.return_code = 0
        return 0

    def kill(self) -> None:
        self.kill_calls += 1
        self.return_code = -9


@dataclass
class FakeFactory:
    process: FakeProcess
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, arguments: tuple[str, ...]) -> FakeProcess:
        self.calls.append(arguments)
        return self.process


def _asset(tmp_path: Path) -> Path:
    path = tmp_path / "alert.wav"
    path.write_bytes(b"RIFF test")
    return path


def test_player_starts_exact_named_device_and_stops_with_sigint(tmp_path: Path) -> None:
    process = FakeProcess()
    factory = FakeFactory(process)
    player = AlsaAudioPlayer(
        config=DEFAULT_CONFIG.audio,
        health=FakeHealth(),
        process_factory=factory,
    )
    asset = _asset(tmp_path)

    player.start(asset)

    assert player.is_playing is True
    assert factory.calls == [
        (
            "/usr/bin/aplay",
            "-q",
            "-D",
            "hw:wm8960soundcard,0",
            str(asset),
        )
    ]
    player.stop()
    assert process.signals == [signal.SIGINT]
    assert process.wait_calls == [2]
    assert player.is_playing is False


def test_player_refuses_implicit_replacement(tmp_path: Path) -> None:
    player = AlsaAudioPlayer(
        config=DEFAULT_CONFIG.audio,
        health=FakeHealth(),
        process_factory=FakeFactory(FakeProcess()),
    )
    asset = _asset(tmp_path)
    player.start(asset)

    with pytest.raises(AudioBusyError):
        player.start(asset)


def test_player_reports_immediate_aplay_failure(tmp_path: Path) -> None:
    player = AlsaAudioPlayer(
        config=DEFAULT_CONFIG.audio,
        health=FakeHealth(),
        process_factory=FakeFactory(FakeProcess(return_code=1)),
    )

    with pytest.raises(AudioProcessError, match="status 1"):
        player.start(_asset(tmp_path))


def test_player_accepts_only_existing_wav_assets(tmp_path: Path) -> None:
    player = AlsaAudioPlayer(
        config=DEFAULT_CONFIG.audio,
        health=FakeHealth(),
        process_factory=FakeFactory(FakeProcess()),
    )

    with pytest.raises(FileNotFoundError):
        player.start(tmp_path / "missing.wav")
    text_asset = tmp_path / "alert.mp3"
    text_asset.write_bytes(b"not audio")
    with pytest.raises(ValueError, match="WAV"):
        player.start(text_asset)
