from __future__ import annotations

from dataclasses import dataclass, field

from asm.infrastructure.audio.alsa_health import AlsaAudioHealth
from asm.infrastructure.audio.commands import CommandResult


@dataclass
class FakeRunner:
    preload: CommandResult
    capture: CommandResult
    playback: CommandResult
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(
        self,
        arguments: tuple[str, ...],
        *,
        timeout_seconds: float = 10.0,
    ) -> CommandResult:
        del timeout_seconds
        self.calls.append(arguments)
        executable = arguments[0]
        if executable.endswith("systemctl"):
            return self.preload
        if executable.endswith("arecord"):
            return self.capture
        return self.playback


def test_health_requires_exact_named_card_and_active_preload() -> None:
    runner = FakeRunner(
        preload=CommandResult(0, "active\n"),
        capture=CommandResult(0, "card 1: wm8960soundcard [wm8960-soundcard]"),
        playback=CommandResult(0, "card 1: wm8960soundcard [wm8960-soundcard]"),
    )
    health = AlsaAudioHealth(
        card_name="wm8960soundcard",
        preload_service="wm8960-audio-board-preload.service",
        runner=runner,
    )

    status = health.read()

    assert status.ready_for_capture is True
    assert status.ready_for_playback is True
    assert len(runner.calls) == 3


def test_failed_preload_fails_closed_even_when_alsa_card_exists() -> None:
    card = CommandResult(0, "card 1: wm8960soundcard")
    health = AlsaAudioHealth(
        card_name="wm8960soundcard",
        preload_service="wm8960-audio-board-preload.service",
        runner=FakeRunner(CommandResult(0, "failed\n"), card, card),
    )

    status = health.read()

    assert status.capture_available is True
    assert status.playback_available is True
    assert status.ready_for_capture is False
    assert status.ready_for_playback is False
