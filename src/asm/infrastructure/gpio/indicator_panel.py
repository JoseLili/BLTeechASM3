"""Active-high GPIO output adapter for Carrier v3.1 Rev A indicators."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, Self

from asm.domain.indicators import Indicator, IndicatorState


class OutputDevice(Protocol):
    def on(self) -> None: ...

    def off(self) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class IndicatorPin:
    indicator: Indicator
    gpio: int


INDICATOR_PINS = (
    IndicatorPin(Indicator.ADVISORY, 23),
    IndicatorPin(Indicator.WATCH, 24),
    IndicatorPin(Indicator.WARNING, 25),
    IndicatorPin(Indicator.POWER, 4),
)


class GpioIndicatorPanel:
    """Apply full states and guarantee an all-off close operation."""

    def __init__(self, *, devices: Mapping[Indicator, OutputDevice]) -> None:
        expected = {pin.indicator for pin in INDICATOR_PINS}
        if set(devices) != expected:
            raise ValueError("devices must contain all four Carrier Rev A indicators")
        self._devices = dict(devices)
        self._closed = False

    @classmethod
    def open(cls) -> Self:
        """Open active-high outputs initially off."""
        try:
            from gpiozero import LED  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError("GPIO support requires Debian package python3-gpiozero") from error

        devices = {
            pin.indicator: LED(pin=pin.gpio, active_high=True, initial_value=False)
            for pin in INDICATOR_PINS
        }
        return cls(devices=devices)

    def apply(self, state: IndicatorState) -> None:
        """Set every output so previous indications cannot leak into a new state."""
        if self._closed:
            raise RuntimeError("indicator panel is closed")
        for indicator, device in self._devices.items():
            if state.is_on(indicator):
                device.on()
            else:
                device.off()

    def close(self) -> None:
        """Turn every indicator off before releasing its GPIO."""
        if self._closed:
            return
        self.apply(IndicatorState())
        self._closed = True
        for device in self._devices.values():
            device.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

