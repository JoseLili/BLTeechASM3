from __future__ import annotations

import os
import subprocess
import sys


def test_command_script_is_importable_with_deployment_pythonpath() -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"

    result = subprocess.run(
        [sys.executable, "scripts/button_command_test.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert "Print one semantic command" in result.stdout
