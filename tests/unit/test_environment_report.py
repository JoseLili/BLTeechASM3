from __future__ import annotations

from pathlib import Path

from scripts.environment_report import _availability, _read_text


def test_read_text_returns_none_for_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing"

    assert _read_text(path) is None


def test_availability_reports_known_module() -> None:
    assert _availability("sys") == "available"


def test_availability_reports_unknown_module() -> None:
    assert _availability("asm_blteech_module_that_does_not_exist") == "not installed"
