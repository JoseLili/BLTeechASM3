"""Capture bounded WM8960 audio and measure exact-zero failure on SA818 input."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from asm.config import DEFAULT_CONFIG
from asm.infrastructure.audio.alsa_health import AlsaAudioHealth
from asm.infrastructure.audio.capture_probe import AlsaCaptureProbe


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=2)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    health = AlsaAudioHealth.open(DEFAULT_CONFIG.audio)
    probe = AlsaCaptureProbe.open(DEFAULT_CONFIG.audio, health)

    with TemporaryDirectory(prefix="asm-audio-") as temporary_directory:
        destination = args.output or Path(temporary_directory) / "capture.wav"
        metrics = probe.capture_wav(destination, duration_seconds=args.seconds)
        print(
            f"CAPTURE frames={metrics.frame_count} rate={metrics.spec.sample_rate_hz} "
            f"channels={metrics.spec.channels} selected={metrics.selected_channel}"
        )
        print(
            f"LEVEL peak={metrics.peak_normalized:.9f} "
            f"rms={metrics.rms_normalized:.9f}"
        )
        if args.output is not None:
            print(f"FILE {destination}")
        if metrics.is_exact_silence:
            print("FAIL selected SA818 channel contains only zero samples")
            return 2
        print("PASS selected SA818 channel contains PCM activity")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
