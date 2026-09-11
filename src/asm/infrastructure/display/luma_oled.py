"""Luma.OLED adapter for the carrier's SSD1306 display.

This module translates a technology-neutral :class:`SystemView` into pixels.
It must not decide system states, priorities, or business transitions.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol, Self

from asm.application.ports import DiagnosticView, MenuView, SystemView
from asm.config.models import BrandingConfig
from asm.infrastructure.display.startup_animation import StartupFrame


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

    def __init__(
        self,
        *,
        device: OledDevice,
        canvas_factory: CanvasFactory,
        branding: BrandingConfig,
    ) -> None:
        self._device = device
        self._canvas_factory = canvas_factory
        self._branding = branding

    @classmethod
    def open(cls, *, branding: BrandingConfig, bus: int = 1, address: int = 0x3C) -> Self:
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
        return cls(device=device, canvas_factory=canvas, branding=branding)

    def show(self, view: SystemView) -> None:
        """Draw one complete frame; Luma swaps it onto the OLED on context exit."""
        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            draw.text((5, 5), _fit(view.title), fill="white")
            draw.line((5, 20, 122, 20), fill="white")
            draw.text((5, 27), _fit(view.detail), fill="white")
            draw.text((5, 47), _fit(f"Estado: {view.state}"), fill="white")

    def show_menu(self, view: MenuView) -> None:
        """Render a four-row scrolling menu with the selected row marked."""
        visible_rows = 4
        max_start = max(0, len(view.items) - visible_rows)
        start = min(max(0, view.selected_index - visible_rows + 1), max_start)
        visible_items = view.items[start : start + visible_rows]

        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            draw.text((3, 1), _fit(view.title, 19), fill="white")
            draw.line((2, 12, 125, 12), fill="white")
            for row, label in enumerate(visible_items):
                absolute_index = start + row
                prefix = ">" if absolute_index == view.selected_index else " "
                draw.text((3, 16 + row * 12), f"{prefix}{_fit(label, 17)}", fill="white")

    def show_diagnostic(self, view: DiagnosticView) -> None:
        """Render an asynchronous diagnostic notice without changing system state."""
        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            draw.text((3, 1), _fit(view.title, 19), fill="white")
            draw.text((102, 1), _fit(view.severity.value, 4), fill="white")
            draw.line((2, 12, 125, 12), fill="white")
            for row, line in enumerate(view.lines):
                draw.text((3, 17 + row * 14), _fit(line, 20), fill="white")

    def show_startup_frame(self, frame: StartupFrame) -> None:
        """Draw one branded frame without changing or interpreting system state."""
        waveform = _waveform_prefix(frame.progress)
        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            draw.text((40, 6), _fit(self._branding.company_name), fill="white")
            if len(waveform) >= 2:
                draw.line(waveform, fill="white")
            product_label = f"{self._branding.product_name} {self._branding.generation}"
            draw.text((42, 39), _fit(product_label), fill="white")
            startup_label = f"{self._branding.startup_text}{'.' * frame.dots}"
            draw.text((32, 51), _fit(startup_label), fill="white")

    def clear(self) -> None:
        """Clear the physical display after an explicit shutdown or smoke test."""
        self._device.clear()


# A compact seismic trace gives the startup sequence a BLTeech identity while
# keeping every frame inexpensive enough for the I2C display.
_WAVEFORM = (
    (7, 29),
    (22, 29),
    (27, 25),
    (32, 34),
    (38, 16),
    (44, 43),
    (51, 23),
    (57, 29),
    (72, 29),
    (77, 26),
    (82, 32),
    (88, 20),
    (94, 38),
    (101, 27),
    (107, 29),
    (121, 29),
)


def _waveform_prefix(progress: float) -> tuple[tuple[int, int], ...]:
    """Reveal the seismic trace from left to right for the current frame."""
    visible_points = max(1, round(progress * (len(_WAVEFORM) - 1)) + 1)
    return _WAVEFORM[:visible_points]
