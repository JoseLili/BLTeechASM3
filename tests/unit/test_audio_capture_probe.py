from __future__ import annotations

import struct
import wave
from dataclasses import dataclass
from pathlib import Path

import pytest

from asm.config import DEFAULT_CONFIG
from asm.domain.audio import AudioDeviceStatus
from asm.infrastructure.audio.capture_probe import AlsaCaptureProbe, analyze_s32le_wav
from asm.infrastructure.audio.commands import CommandResult
from asm.infrastructure.audio.errors import AudioProcessError, AudioUnavailableError


def _write_stereo_wav(path: Path, right_samples: tuple[int, ...]) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(4)
        output.setframerate(48_000)
        frames = b"".join(struct.pack("<ii", 0, sample) for sample in right_samples)
        output.writeframes(frames)


@dataclass
class FakeHealth:
    status: AudioDeviceStatus

    def read(self) -> AudioDeviceStatus:
        return self.status


@dataclass
class RecordingRunner:
    arguments: tuple[str, ...] | None = None
    timeout_seconds: float | None = None

    def __call__(
        self,
        arguments: tuple[str, ...],
        *,
        timeout_seconds: float = 10.0,
    ) -> CommandResult:
        self.arguments = arguments
        self.timeout_seconds = timeout_seconds
        _write_stereo_wav(Path(arguments[-1]), (1_073_741_824, -1_073_741_824))
        return CommandResult(0)


def _status(*, ready: bool) -> AudioDeviceStatus:
    return AudioDeviceStatus(
        card_name="wm8960soundcard",
        preload_ready=ready,
        capture_available=ready,
        playback_available=ready,
    )


def test_analyzer_selects_right_s32_channel_without_threshold(tmp_path: Path) -> None:
    path = tmp_path / "capture.wav"
    _write_stereo_wav(path, (1_073_741_824, -1_073_741_824))

    metrics = analyze_s32le_wav(
        path,
        expected_spec=DEFAULT_CONFIG.audio.capture_spec,
        selected_channel=1,
    )

    assert metrics.frame_count == 2
    assert metrics.selected_channel == 1
    assert metrics.peak_normalized == 0.5
    assert metrics.rms_normalized == 0.5
    assert metrics.is_exact_silence is False


def test_probe_builds_exact_wm8960_capture_command(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "capture.wav"
    runner = RecordingRunner()
    probe = AlsaCaptureProbe(
        config=DEFAULT_CONFIG.audio,
        health=FakeHealth(_status(ready=True)),
        runner=runner,
    )

    metrics = probe.capture_wav(destination, duration_seconds=2)

    assert metrics.frame_count == 2
    assert runner.arguments == (
        "/usr/bin/arecord",
        "-q",
        "-D",
        "hw:wm8960soundcard,0",
        "-f",
        "S32_LE",
        "-r",
        "48000",
        "-c",
        "2",
        "-t",
        "wav",
        "-d",
        "2",
        str(destination),
    )
    assert runner.timeout_seconds == 7.0


def test_probe_fails_closed_before_starting_when_preload_is_unhealthy(
    tmp_path: Path,
) -> None:
    runner = RecordingRunner()
    probe = AlsaCaptureProbe(
        config=DEFAULT_CONFIG.audio,
        health=FakeHealth(_status(ready=False)),
        runner=runner,
    )

    with pytest.raises(AudioUnavailableError):
        probe.capture_wav(tmp_path / "capture.wav", duration_seconds=2)

    assert runner.arguments is None


def test_probe_removes_partial_file_after_arecord_failure(tmp_path: Path) -> None:
    destination = tmp_path / "capture.wav"

    def failed_runner(
        arguments: tuple[str, ...],
        *,
        timeout_seconds: float = 10.0,
    ) -> CommandResult:
        del timeout_seconds
        Path(arguments[-1]).write_bytes(b"partial")
        return CommandResult(1, stderr="device busy")

    probe = AlsaCaptureProbe(
        config=DEFAULT_CONFIG.audio,
        health=FakeHealth(_status(ready=True)),
        runner=failed_runner,
    )

    with pytest.raises(AudioProcessError, match="device busy"):
        probe.capture_wav(destination, duration_seconds=2)

    assert destination.exists() is False
