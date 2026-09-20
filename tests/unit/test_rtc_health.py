from __future__ import annotations

from pathlib import Path

from asm.infrastructure.rtc_health import read_rtc_status


def test_missing_rtc_is_explicit(tmp_path: Path) -> None:
    assert read_rtc_status(tmp_path / "missing").present is False


def test_linux_rtc_fields_are_reported_without_writes(tmp_path: Path) -> None:
    rtc = tmp_path / "rtc0"
    rtc.mkdir()
    (rtc / "name").write_text("rtc-ds1307 1-0068\n", encoding="ascii")
    (rtc / "date").write_text("2026-09-11\n", encoding="ascii")
    (rtc / "time").write_text("23:43:13\n", encoding="ascii")
    (rtc / "hctosys").write_text("1\n", encoding="ascii")

    status = read_rtc_status(rtc)

    assert status.present is True
    assert status.name == "rtc-ds1307 1-0068"
    assert status.date == "2026-09-11"
    assert status.time == "23:43:13"
    assert status.initialized_system_clock is True
    assert status.plausible_time is True
    assert status.ready is True


def test_reset_year_is_degraded_even_when_kernel_reports_hctosys(tmp_path: Path) -> None:
    rtc = tmp_path / "rtc0"
    rtc.mkdir()
    (rtc / "name").write_text("rtc-ds1307 1-0068\n", encoding="ascii")
    (rtc / "date").write_text("2000-01-01\n", encoding="ascii")
    (rtc / "time").write_text("11:37:43\n", encoding="ascii")
    (rtc / "hctosys").write_text("1\n", encoding="ascii")

    status = read_rtc_status(rtc)

    assert status.present is True
    assert status.initialized_system_clock is True
    assert status.plausible_time is False
    assert status.ready is False


def test_invalid_or_empty_rtc_date_is_not_plausible(tmp_path: Path) -> None:
    rtc = tmp_path / "rtc0"
    rtc.mkdir()
    (rtc / "date").write_text("not-a-date\n", encoding="ascii")
    (rtc / "time").write_text("11:37:43\n", encoding="ascii")
    (rtc / "hctosys").write_text("1\n", encoding="ascii")

    assert read_rtc_status(rtc).plausible_time is False
