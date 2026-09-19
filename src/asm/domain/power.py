"""Pure semantic models for the isolated Mean Well status inputs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PowerSignal(StrEnum):
    """Five status signals exposed by J6 on Carrier v3.1 Rev A."""

    AC_OK = "AC_OK"
    BATTERY_DISCONNECTED = "BATTERY_DISCONNECTED"
    BATTERY_LOW = "BATTERY_LOW"
    BATTERY_FULL = "BATTERY_FULL"
    DISCHARGING = "DISCHARGING"


class SignalState(StrEnum):
    """Semantic assertion state; UNKNOWN prevents invented normality."""

    ASSERTED = "ASSERTED"
    CLEAR = "CLEAR"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PowerStatus:
    """One coherent snapshot after electrical polarity translation."""

    ac_ok: SignalState
    battery_disconnected: SignalState
    battery_low: SignalState
    battery_full: SignalState
    discharging: SignalState

    def state_for(self, signal: PowerSignal) -> SignalState:
        """Access a field by semantic signal without exposing GPIO mappings."""
        return {
            PowerSignal.AC_OK: self.ac_ok,
            PowerSignal.BATTERY_DISCONNECTED: self.battery_disconnected,
            PowerSignal.BATTERY_LOW: self.battery_low,
            PowerSignal.BATTERY_FULL: self.battery_full,
            PowerSignal.DISCHARGING: self.discharging,
        }[signal]

    @property
    def asserted_signals(self) -> tuple[PowerSignal, ...]:
        """Return asserted lines without assigning business severity."""
        return tuple(
            signal for signal in PowerSignal if self.state_for(signal) is SignalState.ASSERTED
        )

    @property
    def is_complete(self) -> bool:
        """Report whether every electrical input produced a valid binary value."""
        return all(self.state_for(signal) is not SignalState.UNKNOWN for signal in PowerSignal)

