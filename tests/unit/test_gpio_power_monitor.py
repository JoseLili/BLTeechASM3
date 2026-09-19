from __future__ import annotations

from dataclasses import dataclass

import pytest

from asm.domain.power import PowerSignal, SignalState
from asm.infrastructure.gpio.power_monitor import POWER_SIGNAL_PINS, GpioPowerMonitor


@dataclass
class FakeInput:
    is_active: bool | None
    closes: int = 0

    def close(self) -> None:
        self.closes += 1


def _devices() -> dict[PowerSignal, FakeInput]:
    return {
        PowerSignal.AC_OK: FakeInput(True),
        PowerSignal.BATTERY_DISCONNECTED: FakeInput(False),
        PowerSignal.BATTERY_LOW: FakeInput(True),
        PowerSignal.BATTERY_FULL: FakeInput(False),
        PowerSignal.DISCHARGING: FakeInput(None),
    }


def test_mapping_matches_carrier_revision_a_contract() -> None:
    assert [(pin.signal, pin.gpio) for pin in POWER_SIGNAL_PINS] == [
        (PowerSignal.AC_OK, 5),
        (PowerSignal.BATTERY_DISCONNECTED, 13),
        (PowerSignal.BATTERY_LOW, 26),
        (PowerSignal.BATTERY_FULL, 6),
        (PowerSignal.DISCHARGING, 12),
    ]


def test_read_translates_active_low_and_preserves_unknown() -> None:
    monitor = GpioPowerMonitor(devices=_devices())

    status = monitor.read()

    assert status.ac_ok is SignalState.ASSERTED
    assert status.battery_disconnected is SignalState.CLEAR
    assert status.battery_low is SignalState.ASSERTED
    assert status.battery_full is SignalState.CLEAR
    assert status.discharging is SignalState.UNKNOWN


def test_constructor_requires_exact_signal_inventory() -> None:
    devices = _devices()
    devices.pop(PowerSignal.DISCHARGING)

    with pytest.raises(ValueError, match="all five"):
        GpioPowerMonitor(devices=devices)


def test_close_is_idempotent_and_prevents_further_reads() -> None:
    devices = _devices()
    monitor = GpioPowerMonitor(devices=devices)

    monitor.close()
    monitor.close()

    assert all(device.closes == 1 for device in devices.values())
    with pytest.raises(RuntimeError, match="closed"):
        monitor.read()
