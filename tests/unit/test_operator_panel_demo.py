from __future__ import annotations

import os
import subprocess
import sys


def test_operator_panel_demo_is_importable_without_hardware() -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"

    result = subprocess.run(
        [sys.executable, "scripts/operator_panel_demo.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert "direct operator buttons" in result.stdout
