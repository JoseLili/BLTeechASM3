"""Luma.OLED adapter for the carrier's SSD1306 display.

This module translates a technology-neutral :class:`SystemView` into pixels.
It must not decide system states, priorities, or business transitions.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol, Self

from asm.application.ports import SystemView


class DrawingSurface(Protocol):
    """Small subset of Pillow drawing operations required by this layout."""

    def rectangle(self, xy: object, *, outline: str, fill: str) -> None: ...

    def line(self, xy: object, *, fill: str) -> None: ...

    def text(self, xy: object, text: str, *, fill: str) -> None: ...


class OledDevice(Protocol):
    """Device capabilities used by the adapter and its tests."""

    bounding_box: tuple[int, int, int, int]

    def clear(self) -> None: ...


CanvasFactory = Callable[[OledDevice], AbstractContextManager[DrawingSurface]]


def _fit(text: str, limit: int = 20) -> str:
    """Keep text inside the initial fixed-width 128-pixel layout."""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1]}…"


class LumaOledDisplay:
    """Render semantic system views on the validated 128x64 SSD1306 OLED.

    Use :meth:`open` on Raspberry Pi. Direct construction exists so unit tests
    can inject an in-memory device and canvas without importing Luma.OLED.
    """

    def __init__(self, *, device: OledDevice, canvas_factory: CanvasFactory) -> None:
        self._device = device
        self._canvas_factory = canvas_factory

    @classmethod
    def open(cls, *, bus: int = 1, address: int = 0x3C) -> Self:
        """Open the physical carrier display using its validated I2C values.

        Imports remain local by design: PC simulation and domain tests do not
        require Raspberry Pi packages.
        """
        try:
            from luma.core.interface.serial import i2c  # type: ignore[import-not-found]
            from luma.core.render import canvas  # type: ignore[import-not-found]
            from luma.oled.device import ssd1306  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError(
                "OLED support requires Debian package python3-luma.oled"
            ) from error

        serial = i2c(port=bus, address=address)
        device = ssd1306(serial, width=128, height=64)

        # Luma and Pillow do not publish complete type information. The narrow
        # protocols above keep the untyped boundary confined to this factory.
        return cls(device=device, canvas_factory=canvas)

    def show(self, view: SystemView) -> None:
        """Draw one complete frame; Luma swaps it onto the OLED on context exit."""
        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            draw.text((5, 5), _fit(view.title), fill="white")
            draw.line((5, 20, 122, 20), fill="white")
            draw.text((5, 27), _fit(view.detail), fill="white")
            draw.text((5, 47), _fit(f"Estado: {view.state}"), fill="white")

    def clear(self) -> None:
        """Clear the physical display after an explicit shutdown or smoke test."""
        self._device.clear()
