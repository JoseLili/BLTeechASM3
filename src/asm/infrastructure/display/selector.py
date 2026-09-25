"""Runtime selection between OLED, LCD 16x2, and headless operation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from asm.application.ports import DiagnosticView, MenuView, SystemView
from asm.config.models import BrandingConfig
from asm.infrastructure.display.lcd_16x2 import LCD_DEFAULT_ADDRESSES, Lcd16x2Display
from asm.infrastructure.display.luma_oled import LumaOledDisplay
from asm.infrastructure.display.null_display import NullDisplay
from asm.infrastructure.display.startup_animation import StartupFrame


class RuntimeDisplay(Protocol):
    def show(self, view: SystemView) -> None: ...

    def show_menu(self, view: MenuView) -> None: ...

    def show_diagnostic(self, view: DiagnosticView) -> None: ...

    def show_startup_frame(self, frame: StartupFrame) -> None: ...

    def clear(self) -> None: ...

    def standby(self) -> None: ...


@dataclass(frozen=True, slots=True)
class DisplaySelection:
    display: RuntimeDisplay
    kind: str
    detail: str


DisplayOpener = Callable[[], RuntimeDisplay]


def select_display(
    mode: str,
    *,
    open_oled: DisplayOpener,
    open_lcd: DisplayOpener,
) -> DisplaySelection:
    """Select deterministically; automatic installations prefer an OLED."""
    normalized = mode.lower()
    if normalized == "none":
        return DisplaySelection(NullDisplay(), "none", "headless")
    if normalized == "oled":
        return DisplaySelection(open_oled(), "oled", "configured")
    if normalized == "lcd":
        return DisplaySelection(open_lcd(), "lcd16x2", "configured")
    if normalized != "auto":
        raise ValueError(f"unsupported display mode: {mode}")

    failures: list[str] = []
    try:
        return DisplaySelection(open_oled(), "oled", "auto")
    except Exception as error:
        failures.append(f"OLED={type(error).__name__}:{error}")
    try:
        return DisplaySelection(open_lcd(), "lcd16x2", "auto")
    except Exception as error:
        failures.append(f"LCD={type(error).__name__}:{error}")
    raise RuntimeError("no supported display detected; " + "; ".join(failures))


def open_runtime_display(
    *,
    mode: str,
    branding: BrandingConfig,
    oled_controller: str,
    oled_address: int = 0x3C,
    lcd_address: int | None = None,
    bus: int = 1,
) -> DisplaySelection:
    """Open the selected physical adapter using the carrier I2C bus."""
    lcd_addresses = LCD_DEFAULT_ADDRESSES if lcd_address is None else (lcd_address,)
    selection = select_display(
        mode,
        open_oled=lambda: LumaOledDisplay.open(
            branding=branding,
            bus=bus,
            address=oled_address,
            controller=oled_controller,
        ),
        open_lcd=lambda: Lcd16x2Display.open(
            branding=branding,
            bus=bus,
            addresses=lcd_addresses,
        ),
    )
    if isinstance(selection.display, Lcd16x2Display):
        address = selection.display.address
        detail = f"{selection.detail}:0x{address:02X}" if address is not None else selection.detail
        return DisplaySelection(selection.display, selection.kind, detail)
    if isinstance(selection.display, LumaOledDisplay):
        return DisplaySelection(
            selection.display,
            selection.kind,
            f"{selection.detail}:{oled_controller.lower()}@0x{oled_address:02X}",
        )
    return selection
