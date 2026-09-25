from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from asm.application.ports import DiagnosticView, MenuView, SystemView
from asm.config import DEFAULT_CONFIG
from asm.domain.diagnostics import DiagnosticSeverity
from asm.domain.states import SystemState
from asm.infrastructure.display.lcd_16x2 import (
    Lcd16x2Display,
    Pcf8574Hd44780,
    _lcd_fit,
)
from asm.infrastructure.display.startup_animation import StartupFrame


@dataclass
class FakeCharacterLcd:
    lines: list[tuple[str, str]] = field(default_factory=list)
    backlights: list[bool] = field(default_factory=list)
    clear_calls: int = 0
    close_calls: int = 0

    def write_lines(self, first: str, second: str) -> None:
        self.lines.append((_lcd_fit(first), _lcd_fit(second)))

    def clear(self) -> None:
        self.clear_calls += 1

    def set_backlight(self, enabled: bool) -> None:
        self.backlights.append(enabled)

    def close(self) -> None:
        self.close_calls += 1


@dataclass
class FakeBus:
    present: set[int]
    writes: list[tuple[int, int]] = field(default_factory=list)
    closed: bool = False

    def read_byte(self, address: int) -> int:
        if address not in self.present:
            raise OSError("no ACK")
        return 0xFF

    def write_byte(self, address: int, value: int) -> None:
        self.writes.append((address, value))

    def close(self) -> None:
        self.closed = True


def _display():  # type: ignore[no-untyped-def]
    device = FakeCharacterLcd()
    return Lcd16x2Display(device=device, branding=DEFAULT_CONFIG.branding), device


def test_lcd_normalizes_accents_and_always_fills_sixteen_columns() -> None:
    assert _lcd_fit("  Evacuación sísmica  ") == "Evacuacion sismi"
    assert _lcd_fit("OK") == "OK              "


def test_backpack_detection_accepts_only_reserved_lcd_addresses() -> None:
    bus = FakeBus(present={0x3F})

    assert Pcf8574Hd44780._detect_address(bus, (0x27, 0x3F)) == 0x3F

    with pytest.raises(OSError, match="not detected"):
        Pcf8574Hd44780._detect_address(bus, (0x27,))
    with pytest.raises(ValueError, match="0x27, 0x3F"):
        Pcf8574Hd44780(bus=bus, address=0x20, sleep=lambda _seconds: None)


def test_backpack_initializes_writes_two_rows_and_turns_backlight_off() -> None:
    bus = FakeBus(present={0x27})
    device = Pcf8574Hd44780(
        bus=bus,
        address=0x27,
        sleep=lambda _seconds: None,
        owns_bus=True,
    )

    device.write_lines("ALERTA SISMICA", "Vigencia 5 min")
    device.set_backlight(False)
    device.close()

    assert bus.writes
    assert {address for address, _value in bus.writes} == {0x27}
    assert bus.writes[-1][1] & 0x08 == 0
    assert bus.closed is True


def test_lcd_renders_compact_rwt_footer_on_second_row() -> None:
    display, device = _display()

    display.show(
        SystemView(
            state=SystemState.RWT_ACTIVE,
            title="Esperando evento",
            detail="Escuchando SAME",
            footer="RWT vigente 180m",
            compact=True,
        )
    )

    assert device.lines == [("Esperando evento", "RWT vigente 180m")]


def test_lcd_renders_selected_menu_item_with_position() -> None:
    display, device = _display()

    display.show_menu(
        MenuView(
            title="Menu principal",
            items=("Configuracion", "Estado equipo", "Pruebas"),
            selected_index=1,
        )
    )

    assert device.lines == [("MENU 2/3        ", ">Estado equipo  ")]


def test_lcd_supports_diagnostic_startup_standby_and_close() -> None:
    display, device = _display()

    display.show_diagnostic(
        DiagnosticView(
            title="Audio",
            lines=("Jack disponible",),
            severity=DiagnosticSeverity.INFO,
        )
    )
    display.show_startup_frame(StartupFrame(progress=0.5, dots=2))
    display.standby()
    display.clear()
    display.close()

    assert device.lines[0] == ("Audio           ", "Jack disponible ")
    assert device.lines[1] == ("BLTeech         ", "ASM v3 ..       ")
    assert device.backlights == [False]
    assert device.clear_calls == 1
    assert device.close_calls == 1
