"""HD44780 16x2 adapter using the common PCF8574 I2C backpack."""

from __future__ import annotations

import time
import unicodedata
from collections.abc import Callable
from typing import Protocol, Self

from asm.application.ports import DiagnosticView, MenuView, SystemView
from asm.config.models import BrandingConfig
from asm.infrastructure.display.startup_animation import StartupFrame

LCD_COLUMNS = 16
LCD_ROWS = 2
LCD_DEFAULT_ADDRESSES = (0x27, 0x3F)


class ByteBus(Protocol):
    def read_byte(self, address: int) -> int: ...

    def write_byte(self, address: int, value: int) -> None: ...

    def close(self) -> None: ...


class CharacterLcd(Protocol):
    def write_lines(self, first: str, second: str) -> None: ...

    def clear(self) -> None: ...

    def set_backlight(self, enabled: bool) -> None: ...

    def close(self) -> None: ...


def _lcd_fit(text: str) -> str:
    """Normalize Unicode into the conservative HD44780 ASCII subset."""
    normalized = unicodedata.normalize("NFKD", " ".join(text.split()))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text[:LCD_COLUMNS].ljust(LCD_COLUMNS)


class Pcf8574Hd44780:
    """Write a 4-bit HD44780 through the widespread YwRobot pin mapping."""

    _RS = 0x01
    _ENABLE = 0x04
    _BACKLIGHT = 0x08

    def __init__(
        self,
        *,
        bus: ByteBus,
        address: int,
        sleep: Callable[[float], None] = time.sleep,
        owns_bus: bool = False,
    ) -> None:
        if address not in LCD_DEFAULT_ADDRESSES:
            supported = ", ".join(f"0x{candidate:02X}" for candidate in LCD_DEFAULT_ADDRESSES)
            raise ValueError(f"LCD address must be one of: {supported}")
        self._bus = bus
        self._address = address
        self._sleep = sleep
        self._owns_bus = owns_bus
        self._backlight = True
        self._closed = False
        self._initialize()

    @classmethod
    def open(
        cls,
        *,
        bus_number: int = 1,
        addresses: tuple[int, ...] = LCD_DEFAULT_ADDRESSES,
    ) -> Self:
        try:
            from smbus2 import SMBus  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError("LCD support requires python3-smbus2") from error

        bus = SMBus(bus_number)
        try:
            address = cls._detect_address(bus, addresses)
            return cls(bus=bus, address=address, owns_bus=True)
        except Exception:
            bus.close()
            raise

    @staticmethod
    def _detect_address(bus: ByteBus, addresses: tuple[int, ...]) -> int:
        for address in addresses:
            if address not in LCD_DEFAULT_ADDRESSES:
                continue
            try:
                bus.read_byte(address)
            except OSError:
                continue
            return address
        expected = ", ".join(f"0x{address:02X}" for address in addresses)
        raise OSError(f"LCD 16x2 not detected at {expected}")

    @property
    def address(self) -> int:
        return self._address

    def write_lines(self, first: str, second: str) -> None:
        self.set_backlight(True)
        self._command(0x80)
        for character in _lcd_fit(first):
            self._write_byte(ord(character), rs=True)
        self._command(0xC0)
        for character in _lcd_fit(second):
            self._write_byte(ord(character), rs=True)

    def clear(self) -> None:
        self._command(0x01)
        self._sleep(0.002)

    def set_backlight(self, enabled: bool) -> None:
        self._backlight = enabled
        self._bus.write_byte(self._address, self._BACKLIGHT if enabled else 0x00)

    def close(self) -> None:
        if self._closed:
            return
        try:
            self._backlight = False
            self.clear()
        finally:
            self._closed = True
            if self._owns_bus:
                self._bus.close()

    def _initialize(self) -> None:
        self._sleep(0.05)
        for delay in (0.005, 0.001, 0.001):
            self._write_nibble(0x03, rs=False)
            self._sleep(delay)
        self._write_nibble(0x02, rs=False)
        self._command(0x28)  # 4-bit, two lines, 5x8 font
        self._command(0x08)  # display off while clearing
        self.clear()
        self._command(0x06)  # increment cursor, no display shift
        self._command(0x0C)  # display on, cursor and blink off

    def _command(self, value: int) -> None:
        self._write_byte(value, rs=False)

    def _write_byte(self, value: int, *, rs: bool) -> None:
        self._write_nibble((value >> 4) & 0x0F, rs=rs)
        self._write_nibble(value & 0x0F, rs=rs)

    def _write_nibble(self, nibble: int, *, rs: bool) -> None:
        payload = (nibble << 4) | (self._RS if rs else 0)
        if self._backlight:
            payload |= self._BACKLIGHT
        self._bus.write_byte(self._address, payload | self._ENABLE)
        self._sleep(0.000001)
        self._bus.write_byte(self._address, payload)
        self._sleep(0.00005)


class Lcd16x2Display:
    """Render the shared semantic display contract on two 16-character rows."""

    def __init__(self, *, device: CharacterLcd, branding: BrandingConfig) -> None:
        self._device = device
        self._branding = branding

    @classmethod
    def open(
        cls,
        *,
        branding: BrandingConfig,
        bus: int = 1,
        addresses: tuple[int, ...] = LCD_DEFAULT_ADDRESSES,
    ) -> Self:
        return cls(
            device=Pcf8574Hd44780.open(bus_number=bus, addresses=addresses),
            branding=branding,
        )

    @property
    def address(self) -> int | None:
        return getattr(self._device, "address", None)

    def show(self, view: SystemView) -> None:
        second = view.footer if view.compact and view.footer else view.detail
        self._device.write_lines(view.title, second)

    def show_menu(self, view: MenuView) -> None:
        position = f"MENU {view.selected_index + 1}/{len(view.items)}"
        selected = f">{view.items[view.selected_index]}"
        self._device.write_lines(position, selected)

    def show_diagnostic(self, view: DiagnosticView) -> None:
        self._device.write_lines(view.title, view.lines[0])

    def show_startup_frame(self, frame: StartupFrame) -> None:
        dots = "." * frame.dots
        product = f"{self._branding.product_name} {self._branding.generation}"
        self._device.write_lines(self._branding.company_name, f"{product} {dots}")

    def clear(self) -> None:
        self._device.clear()

    def standby(self) -> None:
        self._device.set_backlight(False)

    def close(self) -> None:
        self._device.close()
