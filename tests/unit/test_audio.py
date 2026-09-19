from __future__ import annotations

import pytest

from asm.domain.audio import (
    AudioCaptureMetrics,
    AudioDeviceStatus,
    AudioStreamSpec,
    PcmSampleFormat,
)


def test_audio_device_readiness_requires_preload_and_direction() -> None:
    status = AudioDeviceStatus("wm8960soundcard", True, True, False)
    assert status.ready_for_capture is True
    assert status.ready_for_playback is False


@pytest.mark.parametrize(("rate", "channels"), [(7_999, 2), (192_001, 2), (48_000, 0)])
def test_stream_spec_rejects_out_of_range_shape(rate: int, channels: int) -> None:
    with pytest.raises(ValueError):
        AudioStreamSpec(PcmSampleFormat.S32_LE, rate, channels)


def test_exact_silence_does_not_invent_an_acoustic_threshold() -> None:
    spec = AudioStreamSpec(PcmSampleFormat.S32_LE, 48_000, 2)
    silence = AudioCaptureMetrics(spec, 10, 1, 0.0, 0.0)
    activity = AudioCaptureMetrics(spec, 10, 1, 1e-12, 1e-13)

    assert silence.is_exact_silence is True
    assert activity.is_exact_silence is False
