"""Read-only Linux RTC evidence for startup logs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

_EARLIEST_PLAUSIBLE_DATE = date(2024, 1, 1)


@dataclass(frozen=True, slots=True)
class RtcStatus:
    present: bool
    name: str = ""
    date: str = ""
    time: str = ""
    initialized_system_clock: bool = False

    @property
    def plausible_time(self) -> bool:
        """Reject reset/default dates even when the kernel reports hctosys."""
        try:
            rtc_date = date.fromisoformat(self.date)
        except ValueError:
            return False
        return rtc_date >= _EARLIEST_PLAUSIBLE_DATE and bool(self.time)

    @property
    def ready(self) -> bool:
        """Require presence, kernel initialization, and a plausible timestamp."""
        return self.present and self.initialized_system_clock and self.plausible_time


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
