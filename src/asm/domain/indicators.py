"""Pure semantic state for the four Carrier Rev A panel indicators."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Indicator(StrEnum):
    """Physical J9 functions without assigning event priority policy."""

    ADVISORY = "ADVISORY"
    WATCH = "WATCH"
    WARNING = "WARNING"
    POWER = "POWER"


@dataclass(frozen=True, slots=True)
class IndicatorState:
    """One complete output state; unspecified stale LEDs cannot survive apply."""

    advisory: bool = False
    watch: bool = False
    warning: bool = False
    power: bool = False

    def is_on(self, indicator: Indicator) -> bool:
        return {
            Indicator.ADVISORY: self.advisory,
            Indicator.WATCH: self.watch,
            Indicator.WARNING: self.warning,
            Indicator.POWER: self.power,
        }[indicator]

    @classmethod
    def only(cls, indicator: Indicator) -> IndicatorState:
        """Create a one-hot state used by diagnostics and lamp tests."""
        return cls(
            advisory=indicator is Indicator.ADVISORY,
            watch=indicator is Indicator.WATCH,
            warning=indicator is Indicator.WARNING,
            power=indicator is Indicator.POWER,
        )

