from __future__ import annotations

from scripts.button_smoke_test import _electrical_level, _parser


def test_button_smoke_defaults_target_simulacro() -> None:
    args = _parser().parse_args([])

    assert args.gpio == 17
    assert args.name == "Simulacro"
    assert args.timeout == 30.0


def test_active_low_level_labels_are_explicit() -> None:
    assert _electrical_level(is_pressed=False) == "HIGH"
    assert _electrical_level(is_pressed=True) == "LOW"
