from __future__ import annotations

import subprocess
import sys


def test_console_demo_reaches_stopped() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "asm"],
        check=True,
        capture_output=True,
        text=True,
    )

    display_lines = [line for line in result.stdout.splitlines() if line.startswith("[DISPLAY]")]
    assert len(display_lines) == 5
    assert "BOOT" in display_lines[0]
    assert "STOPPED" in display_lines[-1]
