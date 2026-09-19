"""Read-only Linux RTC evidence for startup logs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RtcStatus:
    present: bool
    name: str = ""
    date: str = ""
    time: str = ""
    initialized_system_clock: bool = False


def read_rtc_status(root: Path = Path("/sys/class/rtc/rtc0")) -> RtcStatus:
    """Read sysfs only; the kernel remains responsible for hctosys."""
    if not root.is_dir():
        return RtcStatus(present=False)

    def read(name: str) -> str:
        try:
            return (root / name).read_text(encoding="ascii").strip()
        except OSError:
            return ""

    return RtcStatus(
        present=True,
        name=read("name"),
        date=read("date"),
        time=read("time"),
        initialized_system_clock=read("hctosys") == "1",
    )
