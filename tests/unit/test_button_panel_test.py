from __future__ import annotations

import os
import subprocess
import sys

from scripts.button_panel_test import BUTTONS, _parser


def test_panel_inventory_matches_current_carrier_mapping() -> None:
    assert [(button.name, button.gpio) for button in BUTTONS] == [
        ("Simulacro", 17),
        ("Paro", 27),
        ("Evacuacion", 22),
    ]


def test_panel_test_default_timeout_allows_manual_interaction() -> None:
    assert _parser().parse_args([]).timeout == 120.0


def test_panel_script_is_importable_with_deployment_pythonpath() -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"

    result = subprocess.run(
        [sys.executable, "scripts/button_panel_test.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert "Validate all three" in result.stdout
