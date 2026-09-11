"""Pure semantic models for the WM8960 audio boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PcmSampleFormat(StrEnum):
    """ALSA sample encodings required by the current hardware contract."""

    S16_LE = "S16_LE"
    S32_LE = "S32_LE"


@dataclass(frozen=True, slots=True)
class AudioStreamSpec:
    """Technology-neutral PCM shape."""

    sample_format: PcmSampleFormat
    sample_rate_hz: int
    channels: int

    def __post_init__(self) -> None:
        if not 8_000 <= self.sample_rate_hz <= 192_000:
            raise ValueError("sample_rate_hz must be between 8000 and 192000")
        if not 1 <= self.channels <= 8:
            raise ValueError("channels must be between 1 and 8")


@dataclass(frozen=True, slots=True)
class AudioDeviceStatus:
    """Readiness facts that do not claim that captured samples are useful."""

    card_name: str
    preload_ready: bool
    capture_available: bool
    playback_available: bool

    def __post_init__(self) -> None:
        if not self.card_name.strip():
            raise ValueError("card_name must not be empty")

    @property
    def ready_for_capture(self) -> bool:
        return self.preload_ready and self.capture_available

    @property
    def ready_for_playback(self) -> bool:
        return self.preload_ready and self.playback_available


@dataclass(frozen=True, slots=True)
class AudioCaptureMetrics:
    """Measured samples from one bounded diagnostic capture."""

    spec: AudioStreamSpec
    frame_count: int
    selected_channel: int
    peak_normalized: float
    rms_normalized: float

    def __post_init__(self) -> None:
        if self.frame_count < 0:
            raise ValueError("frame_count must not be negative")
        if not 0 <= self.selected_channel < self.spec.channels:
            raise ValueError("selected_channel must reference an available channel")
        if not 0 <= self.peak_normalized <= 1:
            raise ValueError("peak_normalized must be between zero and one")
        if not 0 <= self.rms_normalized <= 1:
            raise ValueError("rms_normalized must be between zero and one")

    @property
    def is_exact_silence(self) -> bool:
        """Detect the all-zero failure without inventing an acoustic threshold."""
        return self.peak_normalized == 0
