from __future__ import annotations

from dataclasses import dataclass

import pytest

from asm.domain.indicators import Indicator, IndicatorState
from asm.infrastructure.gpio.indicator_panel import INDICATOR_PINS, GpioIndicatorPanel


@dataclass
class FakeOutput:
    active: bool = False
    on_calls: int = 0
    off_calls: int = 0
    close_calls: int = 0

    def on(self) -> None:
        self.active = True
        self.on_calls += 1

    def off(self) -> None:
        self.active = False
        self.off_calls += 1

    def close(self) -> None:
        self.close_calls += 1


def _devices() -> dict[Indicator, FakeOutput]:
    return {indicator: FakeOutput() for indicator in Indicator}


def test_mapping_matches_carrier_revision_a_contract() -> None:
    assert [(pin.indicator, pin.gpio) for pin in INDICATOR_PINS] == [
        (Indicator.ADVISORY, 23),
        (Indicator.WATCH, 24),
        (Indicator.WARNING, 25),
        (Indicator.POWER, 4),
    ]


def test_apply_sets_complete_state_and_clears_stale_outputs() -> None:
    devices = _devices()
    panel = GpioIndicatorPanel(devices=devices)

    panel.apply(IndicatorState(advisory=True, warning=True))
    panel.apply(IndicatorState(power=True))

    assert devices[Indicator.ADVISORY].active is False
    assert devices[Indicator.WATCH].active is False
    assert devices[Indicator.WARNING].active is False
    assert devices[Indicator.POWER].active is True


def test_constructor_requires_exact_inventory() -> None:
    devices = _devices()
    devices.pop(Indicator.POWER)

    with pytest.raises(ValueError, match="all four"):
        GpioIndicatorPanel(devices=devices)


def test_close_turns_every_output_off_once_and_releases_devices() -> None:
    devices = _devices()
    panel = GpioIndicatorPanel(devices=devices)
    panel.apply(IndicatorState(warning=True))

    panel.close()
    panel.close()

    assert not any(device.active for device in devices.values())
    assert all(device.close_calls == 1 for device in devices.values())
    with pytest.raises(RuntimeError, match="closed"):
        panel.apply(IndicatorState())
