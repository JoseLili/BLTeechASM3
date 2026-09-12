from __future__ import annotations

from asm.config import DEFAULT_CONFIG
from asm.infrastructure.audio.same_stream import build_same_pipeline_commands


def test_pipeline_matches_validated_wm8960_gold_contract() -> None:
    commands = build_same_pipeline_commands(DEFAULT_CONFIG.audio)

    assert commands.capture == (
        "/usr/bin/arecord",
        "-q",
        "-D",
        "hw:wm8960soundcard,0",
        "-t",
        "raw",
        "-f",
        "S32_LE",
        "-r",
        "48000",
        "-c",
        "2",
    )
    assert commands.convert[-3:] == ("-", "remix", "2")
    assert commands.convert[17:19] == ("-b", "16")
    assert commands.convert[20:22] == ("-r", "22050")
    assert commands.convert[22:24] == ("-c", "1")
    assert commands.decode == ("/usr/bin/multimon-ng", "-a", "EAS", "-t", "raw", "-")
