"""Cancelable BLTeech startup animation, independent from domain events.

Alert, drill, evacuation, and RWT views must bypass this animation. The
animation checks for cancellation before every frame so a future event loop can
replace it immediately with a higher-priority static view.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StartupFrame:
    """Technology-neutral description of one branded animation frame."""

    progress: float
    dots: int

    def __post_init__(self) -> None:
        if not 0.0 <= self.progress <= 1.0:
            raise ValueError("progress must be between zero and one")
        if not 0 <= self.dots <= 3:
            raise ValueError("dots must be between zero and three")


class StartupFrameDisplay(Protocol):
    """Display capability required only by the startup animator."""

    def show_startup_frame(self, frame: StartupFrame) -> None: ...


class StartupAnimator:
    """Play the short brand sequence without owning application state."""

    def __init__(
        self,
        *,
        display: StartupFrameDisplay,
        sleep: Callable[[float], None],
        frame_seconds: float = 0.09,
    ) -> None:
        if frame_seconds <= 0:
            raise ValueError("frame_seconds must be greater than zero")
        self._display = display
        self._sleep = sleep
        self._frame_seconds = frame_seconds

    def play(self, *, cancelled: Callable[[], bool] = lambda: False) -> bool:
        """Play all frames, returning false when a caller interrupts playback."""
        for frame in _FRAMES:
            # Cancellation is checked before drawing, so a priority event never
            # waits for the remaining animation sequence.
            if cancelled():
                return False
            self._display.show_startup_frame(frame)
            self._sleep(self._frame_seconds)
        return True


# Twelve frames keep the sequence close to one second on the physical OLED.
_FRAMES = tuple(
    StartupFrame(progress=index / 11, dots=min(3, index // 3)) for index in range(12)
)
