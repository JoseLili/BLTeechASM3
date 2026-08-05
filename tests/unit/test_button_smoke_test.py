from __future__ import annotations

from asm.infrastructure.gpio.levels import active_low_level
from scripts.button_smoke_test import _parser


def test_button_smoke_defaults_target_simulacro() -> None:
    args = _parser().parse_args([])

    assert args.gpio == 17
    assert args.name == "Simulacro"
    assert args.timeout == 30.0


def test_active_low_level_labels_are_explicit() -> None:
    assert active_low_level(is_active=False) == "HIGH"
    assert active_low_level(is_active=True) == "LOW"
