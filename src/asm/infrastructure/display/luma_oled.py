"""Luma.OLED adapter for the carrier's 128x64 monochrome display.

This module translates a technology-neutral :class:`SystemView` into pixels.
It must not decide system states, priorities, or business transitions.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol, Self

from asm.application.ports import DiagnosticView, MenuView, SystemView
from asm.config.models import BrandingConfig
from asm.domain.states import SystemState
from asm.infrastructure.display.startup_animation import StartupFrame


class DrawingSurface(Protocol):
    """Small subset of Pillow drawing operations required by this layout."""

    def rectangle(self, xy: object, *, outline: str, fill: str) -> None: ...

    def line(self, xy: object, *, fill: str) -> None: ...

    def text(self, xy: object, text: str, *, fill: str, font: object | None = None) -> None: ...


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


def _split_label(text: str, *, line_limit: int = 14) -> tuple[str, ...]:
    """Split one selected menu label into at most two readable lines."""
    normalized = " ".join(text.split())
    if len(normalized) <= line_limit:
        return (normalized,)

    words = normalized.split()
    first: list[str] = []
    while words:
        candidate = " ".join((*first, words[0]))
        if first and len(candidate) > line_limit:
            break
        first.append(words.pop(0))
        if len(candidate) >= line_limit:
            break

    first_line = " ".join(first)
    remainder = " ".join(words)
    if not remainder:
        return (_fit(first_line, line_limit),)
    return (_fit(first_line, line_limit), _fit(remainder, line_limit))


class LumaOledDisplay:
    """Render semantic system views on a 128x64 SSD1306 or SH1106 OLED.

    Use :meth:`open` on Raspberry Pi. Direct construction exists so unit tests
    can inject an in-memory device and canvas without importing Luma.OLED.
    """

    def __init__(
        self,
        *,
        device: OledDevice,
        canvas_factory: CanvasFactory,
        branding: BrandingConfig,
        small_font: object | None = None,
        medium_font: object | None = None,
        large_font: object | None = None,
    ) -> None:
        self._device = device
        self._canvas_factory = canvas_factory
        self._branding = branding
        self._small_font = small_font
        self._medium_font = medium_font
        self._large_font = large_font

    @classmethod
    def open(
        cls,
        *,
        branding: BrandingConfig,
        bus: int = 1,
        address: int = 0x3C,
        controller: str = "sh1106",
    ) -> Self:
        """Open the physical display using its I2C values and controller.

        Imports remain local by design: PC simulation and domain tests do not
        require Raspberry Pi packages.
        """
        try:
            from luma.core.interface.serial import i2c  # type: ignore[import-not-found]
            from luma.core.render import canvas  # type: ignore[import-not-found]
            from luma.oled.device import sh1106, ssd1306  # type: ignore[import-not-found]
            from PIL import ImageFont  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError(
                "OLED support requires Debian package python3-luma.oled"
            ) from error

        serial = i2c(port=bus, address=address)
        device_types = {"ssd1306": ssd1306, "sh1106": sh1106}
        try:
            device_type = device_types[controller.lower()]
        except KeyError as error:
            raise ValueError(f"unsupported OLED controller: {controller}") from error
        device = device_type(serial, width=128, height=64)
        try:
            small_font = ImageFont.truetype("DejaVuSans.ttf", 10)
            medium_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            large_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        except OSError:
            # Minimal Raspberry Pi images may not include DejaVu. The Pillow
            # bitmap font keeps the display operational, albeit less legible.
            small_font = medium_font = large_font = ImageFont.load_default()

        # Luma and Pillow do not publish complete type information. The narrow
        # protocols above keep the untyped boundary confined to this factory.
        return cls(
            device=device,
            canvas_factory=canvas,
            branding=branding,
            small_font=small_font,
            medium_font=medium_font,
            large_font=large_font,
        )

    def show(self, view: SystemView) -> None:
        """Draw a sparse, readable operational frame for the small OLED."""
        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            if (
                view.state in (SystemState.RWT_ACTIVE, SystemState.EQW_ACTIVE)
                and not view.compact
            ):
                self._draw_alert(draw, view)
                return

            draw.text(
                (3, 2),
                _fit(view.title, 16),
                fill="white",
                font=self._medium_font,
            )
            draw.line((3, 20, 124, 20), fill="white")
            draw.text(
                (3, 27),
                _fit(view.detail, 19),
                fill="white",
                font=self._small_font,
            )
            draw.text(
                (3, 49),
                _fit(view.footer or f"ESTADO {view.state}", 20),
                fill="white",
                font=self._small_font,
            )

    def show_menu(self, view: MenuView) -> None:
        """Render one large selected option instead of four tiny rows."""
        selected = view.items[view.selected_index]
        lines = _split_label(selected)
        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            draw.text(
                (2, 1),
                _fit(view.title, 17),
                fill="white",
                font=self._small_font,
            )
            draw.text(
                (103, 1),
                f"{view.selected_index + 1}/{len(view.items)}",
                fill="white",
                font=self._small_font,
            )
            draw.line((2, 13, 125, 13), fill="white")
            start_y = 20 if len(lines) == 2 else 27
            for row, label in enumerate(lines):
                draw.text(
                    (7, start_y + row * 17),
                    f"> {label}" if row == 0 else f"  {label}",
                    fill="white",
                    font=self._medium_font,
                )
            draw.text((3, 53), "^/v MOVER   OK >", fill="white", font=self._small_font)

    def show_diagnostic(self, view: DiagnosticView) -> None:
        """Render an asynchronous diagnostic notice without changing system state."""
        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            draw.text(
                (3, 1),
                _fit(view.title, 16),
                fill="white",
                font=self._small_font,
            )
            draw.text(
                (100, 1),
                _fit(view.severity.value, 4),
                fill="white",
                font=self._small_font,
            )
            draw.line((2, 13, 125, 13), fill="white")
            for row, line in enumerate(view.lines):
                draw.text(
                    (3, 18 + row * 14),
                    _fit(line, 20),
                    fill="white",
                    font=self._small_font,
                )

    def show_startup_frame(self, frame: StartupFrame) -> None:
        """Draw one branded frame without changing or interpreting system state."""
        waveform = _waveform_prefix(frame.progress)
        with self._canvas_factory(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="black")
            draw.text(
                (37, 3),
                _fit(self._branding.company_name),
                fill="white",
                font=self._medium_font,
            )
            if len(waveform) >= 2:
                draw.line(waveform, fill="white")
            product_label = f"{self._branding.product_name} {self._branding.generation}"
            draw.text((42, 39), _fit(product_label), fill="white", font=self._small_font)
            startup_label = f"{self._branding.startup_text}{'.' * frame.dots}"
            draw.text((32, 51), _fit(startup_label), fill="white", font=self._small_font)

    def _draw_alert(self, draw: DrawingSurface, view: SystemView) -> None:
        """Give RWT and EQW the largest text while retaining validity."""
        if view.state is SystemState.EQW_ACTIVE:
            draw.text((5, -2), "ALERTA", fill="white", font=self._large_font)
            draw.text((5, 17), "SISMICA", fill="white", font=self._large_font)
            detail_y = 43
            footer = "WARNING ACTIVO"
        else:
            draw.text((5, 3), "AVISO RWT", fill="white", font=self._large_font)
            detail_y = 30
            footer = "ADVISORY ACTIVO"

        draw.text(
            (5, detail_y),
            _fit(view.detail, 20),
            fill="white",
            font=self._small_font,
        )
        draw.text((5, 53), footer, fill="white", font=self._small_font)

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
