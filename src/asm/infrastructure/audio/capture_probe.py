"""Bounded WM8960 WAV capture and exact-zero activity measurement."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from asm.application.ports import AudioHealthPort
from asm.config.models import AudioConfig
from asm.domain.audio import AudioCaptureMetrics, AudioStreamSpec, PcmSampleFormat
from asm.infrastructure.audio.commands import CommandRunner, run_command
from asm.infrastructure.audio.errors import AudioProcessError, AudioUnavailableError


class AlsaCaptureProbe:
    """Record a finite diagnostic WAV; it is not the future decoder stream."""

    def __init__(
        self,
        *,
        config: AudioConfig,
        health: AudioHealthPort,
        runner: CommandRunner,
    ) -> None:
        self._config = config
        self._health = health
        self._runner = runner

    @classmethod
    def open(cls, config: AudioConfig, health: AudioHealthPort) -> AlsaCaptureProbe:
        return cls(config=config, health=health, runner=run_command)

    def capture_wav(self, destination: Path, *, duration_seconds: int) -> AudioCaptureMetrics:
        if not 1 <= duration_seconds <= 300:
            raise ValueError("duration_seconds must be between 1 and 300")
        if destination.exists():
            raise FileExistsError(destination)
        if not self._health.read().ready_for_capture:
            raise AudioUnavailableError("WM8960 capture or preload is unavailable")

        destination.parent.mkdir(parents=True, exist_ok=True)
        spec = self._config.capture_spec
        result = self._runner(
            (
                "/usr/bin/arecord",
                "-q",
                "-D",
                self._config.pcm_device,
                "-f",
                spec.sample_format.value,
                "-r",
                str(spec.sample_rate_hz),
                "-c",
                str(spec.channels),
                "-t",
                "wav",
                "-d",
                str(duration_seconds),
                str(destination),
            ),
            timeout_seconds=duration_seconds + 5.0,
        )
        if result.returncode != 0:
            destination.unlink(missing_ok=True)
            raise AudioProcessError(result.stderr.strip() or "arecord failed")
        return analyze_s32le_wav(
            destination,
            expected_spec=spec,
            selected_channel=self._config.radio_capture_channel,
        )


def analyze_s32le_wav(
    path: Path,
    *,
    expected_spec: AudioStreamSpec,
    selected_channel: int,
) -> AudioCaptureMetrics:
    """Measure one interleaved channel without defining a signal threshold."""
    if expected_spec.sample_format is not PcmSampleFormat.S32_LE:
        raise ValueError("capture analyzer currently requires S32_LE")

    peak = 0
    sum_squares = 0
    sample_count = 0
    with wave.open(str(path), "rb") as recording:
        actual_spec = AudioStreamSpec(
            sample_format=PcmSampleFormat.S32_LE,
            sample_rate_hz=recording.getframerate(),
            channels=recording.getnchannels(),
        )
        if recording.getsampwidth() != 4 or actual_spec != expected_spec:
            raise AudioProcessError("captured WAV does not match the requested PCM spec")
        frame_count = recording.getnframes()
        while data := recording.readframes(4096):
            for index, (sample,) in enumerate(struct.iter_unpack("<i", data)):
                if index % actual_spec.channels != selected_channel:
                    continue
                magnitude = abs(sample)
                peak = max(peak, magnitude)
                sum_squares += sample * sample
                sample_count += 1

    full_scale = 2_147_483_648.0
    rms = math.sqrt(sum_squares / sample_count) / full_scale if sample_count else 0.0
    return AudioCaptureMetrics(
        spec=actual_spec,
        frame_count=frame_count,
        selected_channel=selected_channel,
        peak_normalized=peak / full_scale,
        rms_normalized=rms,
    )
