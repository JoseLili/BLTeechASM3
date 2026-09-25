from __future__ import annotations

from dataclasses import dataclass

import pytest

from asm.infrastructure.display.selector import select_display


@dataclass
class FakeDisplay:
    name: str


def test_auto_prefers_oled_when_both_are_available() -> None:
    oled = FakeDisplay("oled")
    lcd = FakeDisplay("lcd")

    selected = select_display(  # type: ignore[arg-type]
        "auto",
        open_oled=lambda: oled,
        open_lcd=lambda: lcd,
    )

    assert selected.display is oled
    assert selected.kind == "oled"


def test_auto_falls_back_to_lcd_16x2_when_oled_is_absent() -> None:
    lcd = FakeDisplay("lcd")

    def missing_oled():  # type: ignore[no-untyped-def]
        raise OSError("no ACK")

    selected = select_display(  # type: ignore[arg-type]
        "auto",
        open_oled=missing_oled,
        open_lcd=lambda: lcd,
    )

    assert selected.display is lcd
    assert selected.kind == "lcd16x2"


def test_explicit_lcd_does_not_probe_oled() -> None:
    lcd = FakeDisplay("lcd")

    selected = select_display(  # type: ignore[arg-type]
        "lcd",
        open_oled=lambda: pytest.fail("OLED must not be opened"),
        open_lcd=lambda: lcd,
    )

    assert selected.display is lcd


def test_auto_reports_both_detection_failures() -> None:
    def fail_oled():  # type: ignore[no-untyped-def]
        raise OSError("OLED missing")

    def fail_lcd():  # type: ignore[no-untyped-def]
        raise OSError("LCD missing")

    with pytest.raises(RuntimeError, match="no supported display detected"):
        select_display("auto", open_oled=fail_oled, open_lcd=fail_lcd)
