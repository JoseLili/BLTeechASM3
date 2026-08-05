from __future__ import annotations

from scripts.button_panel_test import BUTTONS, _parser


def test_panel_inventory_matches_current_carrier_mapping() -> None:
    assert [(button.name, button.gpio) for button in BUTTONS] == [
        ("Simulacro", 17),
        ("Paro", 27),
        ("Evacuacion", 22),
    ]


def test_panel_test_default_timeout_allows_manual_interaction() -> None:
    assert _parser().parse_args([]).timeout == 120.0
