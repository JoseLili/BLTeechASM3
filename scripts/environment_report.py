"""Print a read-only environment report for development and Raspberry Pi hosts."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from pathlib import Path


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").replace("\x00", "").strip()
    except (OSError, UnicodeError):
        return None


def _availability(module: str) -> str:
    return "available" if importlib.util.find_spec(module) is not None else "not installed"


def _virtual_environment() -> str:
    configured = os.environ.get("VIRTUAL_ENV")
    if configured:
        return configured
    if sys.prefix != sys.base_prefix:
        return sys.prefix
    return "not active"


def main() -> None:
    """Emit facts only; the report never changes host configuration."""
    model = _read_text(Path("/proc/device-tree/model")) or "not detected"
    i2c_nodes = sorted(str(path) for path in Path("/dev").glob("i2c-*"))

    report = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "raspberry_pi_model": model,
        "i2c_devices": ", ".join(i2c_nodes) if i2c_nodes else "none visible",
        "virtual_environment": _virtual_environment(),
        "pytest": _availability("pytest"),
        "ruff": _availability("ruff"),
        "mypy": _availability("mypy"),
    }

    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
