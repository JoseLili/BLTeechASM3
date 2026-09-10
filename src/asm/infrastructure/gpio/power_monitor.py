"""Active-low GPIO adapter for Carrier v3.1 Rev A power-status optocouplers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, Self

from asm.domain.power import PowerSignal, PowerStatus, SignalState


class InputDevice(Protocol):
    """Minimal gpiozero-compatible input surface used by the adapter."""

    @property
    def is_active(self) -> bool | None: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class PowerSignalPin:
    """Frozen J6 semantic signal to Raspberry Pi BCM mapping."""

    signal: PowerSignal
    gpio: int


POWER_SIGNAL_PINS = (
    PowerSignalPin(PowerSignal.AC_OK, 5),
    PowerSignalPin(PowerSignal.BATTERY_DISCONNECTED, 13),
    PowerSignalPin(PowerSignal.BATTERY_LOW, 26),
    PowerSignalPin(PowerSignal.BATTERY_FULL, 6),
    PowerSignalPin(PowerSignal.DISCHARGING, 12),
)


class GpioPowerMonitor:
    """Translate one simultaneous-looking input snapshot into semantic states."""

    def __init__(self, *, devices: Mapping[PowerSignal, InputDevice]) -> None:
        expected = {pin.signal for pin in POWER_SIGNAL_PINS}
        if set(devices) != expected:
            raise ValueError("devices must contain all five Carrier Rev A power signals")
        self._devices = dict(devices)
        self._closed = False

    @classmethod
    def open(cls) -> Self:
        """Open all inputs with pull-ups; PC817 assertion drives them LOW."""
        try:
            from gpiozero import DigitalInputDevice  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError("GPIO support requires Debian package python3-gpiozero") from error

        devices = {
            pin.signal: DigitalInputDevice(pin=pin.gpio, pull_up=True)
            for pin in POWER_SIGNAL_PINS
        }
        return cls(devices=devices)

    def read(self) -> PowerStatus:
        """Read every pin once and stop electrical polarity at this boundary."""
        if self._closed:
            raise RuntimeError("power monitor is closed")
        states = {
            signal: _assertion_state(device.is_active)
            for signal, device in self._devices.items()
        }
        return PowerStatus(
            ac_ok=states[PowerSignal.AC_OK],
            battery_disconnected=states[PowerSignal.BATTERY_DISCONNECTED],
            battery_low=states[PowerSignal.BATTERY_LOW],
            battery_full=states[PowerSignal.BATTERY_FULL],
            discharging=states[PowerSignal.DISCHARGING],
        )

    def close(self) -> None:
        """Release all five GPIO lines exactly once."""
        if self._closed:
            return
        self._closed = True
        for device in self._devices.values():
            device.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


def _assertion_state(is_active: bool | None) -> SignalState:
    # gpiozero applies the pull-up/active-low translation before exposing
    # is_active. Reading .value as a raw voltage would invert the result twice.
    if is_active is True:
        return SignalState.ASSERTED
    if is_active is False:
        return SignalState.CLEAR
    return SignalState.UNKNOWN
