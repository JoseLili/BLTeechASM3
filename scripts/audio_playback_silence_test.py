"""Exercise interruptible WM8960 playback using a low-risk silent WAV."""

from __future__ import annotations

import argparse
import time
import wave
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from asm.config import DEFAULT_CONFIG
from asm.infrastructure.audio.alsa_health import AlsaAudioHealth
from asm.infrastructure.audio.alsa_player import AlsaAudioPlayer


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=1)
    return parser


def _write_silence(path: Path, seconds: int) -> None:
    spec = DEFAULT_CONFIG.audio.capture_spec
    with wave.open(str(path), "wb") as output:
        output.setnchannels(spec.channels)
        output.setsampwidth(4)
        output.setframerate(spec.sample_rate_hz)
        output.writeframes(b"\0" * (spec.sample_rate_hz * spec.channels * 4 * seconds))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not 1 <= args.seconds <= 10:
        raise SystemExit("--seconds must be between 1 and 10")

    health = AlsaAudioHealth.open(DEFAULT_CONFIG.audio)
    with TemporaryDirectory(prefix="asm-audio-") as temporary_directory:
        asset = Path(temporary_directory) / "silence.wav"
        _write_silence(asset, args.seconds)
        with AlsaAudioPlayer.open(DEFAULT_CONFIG.audio, health) as player:
            player.start(asset)
            deadline = time.monotonic() + args.seconds + 2
            while player.is_playing and time.monotonic() < deadline:
                time.sleep(0.01)
            if player.is_playing:
                print("FAIL playback did not finish within its bounded deadline")
                return 2
    print("PASS silent WM8960 WAV playback completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
