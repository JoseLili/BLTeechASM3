from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from asm.infrastructure.display.startup_animation import StartupAnimator, StartupFrame


@dataclass(slots=True)
class CapturingDisplay:
    frames: list[StartupFrame] = field(default_factory=list)

    def show_startup_frame(self, frame: StartupFrame) -> None:
        self.frames.append(frame)


def test_startup_animation_reaches_complete_frame() -> None:
    display = CapturingDisplay()
    sleeps: list[float] = []
    animator = StartupAnimator(display=display, sleep=sleeps.append, frame_seconds=0.05)

    completed = animator.play()

    assert completed is True
    assert len(display.frames) == 12
    assert display.frames[0].progress == 0.0
    assert display.frames[-1].progress == 1.0
    assert display.frames[-1].dots == 3
    assert sleeps == [0.05] * 12


def test_startup_animation_stops_before_next_frame_when_cancelled() -> None:
    display = CapturingDisplay()
    cancellation_checks = 0

    def cancelled() -> bool:
        nonlocal cancellation_checks
        cancellation_checks += 1
        return cancellation_checks > 4

    animator = StartupAnimator(display=display, sleep=lambda _seconds: None)

    completed = animator.play(cancelled=cancelled)

    assert completed is False
    assert len(display.frames) == 4


@pytest.mark.parametrize(
    ("progress", "dots"),
    [(-0.1, 0), (1.1, 0), (0.5, -1), (0.5, 4)],
)
def test_startup_frame_rejects_invalid_values(progress: float, dots: int) -> None:
    with pytest.raises(ValueError):
        StartupFrame(progress=progress, dots=dots)


def test_startup_animation_rejects_non_positive_frame_time() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        StartupAnimator(display=CapturingDisplay(), sleep=lambda _seconds: None, frame_seconds=0)
