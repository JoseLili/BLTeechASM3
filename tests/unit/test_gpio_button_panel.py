from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

import pytest

from asm.application.button_policy import ButtonCommand, PanelButton
from asm.config import DEFAULT_CONFIG, ActivationMode, ConfigurableButtonAction
from asm.infrastructure.gpio.button_panel import BUTTON_PINS, ButtonDevice, GpioButtonPanel


@dataclass(slots=True)
class FakeButtonDevice:
    when_pressed: Callable[[], None] | None = None
    when_released: Callable[[], None] | None = None
    closed: bool = False

    def press(self) -> None:
        assert self.when_pressed is not None
        self.when_pressed()

    def release(self) -> None:
        assert self.when_released is not None
        self.when_released()

    def close(self) -> None:
        self.closed = True


@dataclass(slots=True)
class FakeMonotonic:
    current: float = 0.0

    def __call__(self) -> float:
        return self.current


def _devices() -> dict[PanelButton, FakeButtonDevice]:
    return {button: FakeButtonDevice() for button in PanelButton}


def test_adapter_mapping_matches_validated_carrier() -> None:
    assert [(pin.button, pin.gpio) for pin in BUTTON_PINS] == [
        (PanelButton.SIMULACRO, 17),
        (PanelButton.STOP, 27),
        (PanelButton.EVACUACION, 22),
    ]


def test_every_factory_default_button_emits_its_semantic_command() -> None:
    devices = _devices()
    observed: list[ButtonCommand] = []
    panel = GpioButtonPanel(
        devices=devices,
        config=DEFAULT_CONFIG.buttons,
        monotonic=FakeMonotonic(),
        on_command=observed.append,
    )

    for device in devices.values():
        device.press()
        device.release()

    assert observed == [
        ButtonCommand.START_SIMULACRO,
        ButtonCommand.STOP,
        ButtonCommand.START_EVACUACION,
    ]
    panel.close()
    assert all(device.closed for device in devices.values())


def test_hold_policy_emits_only_after_poll_reaches_threshold() -> None:
    hold = ConfigurableButtonAction(mode=ActivationMode.HOLD, hold_seconds=5.0)
    config = replace(DEFAULT_CONFIG.buttons, simulacro=hold)
    devices = _devices()
    clock = FakeMonotonic(current=10.0)
    observed: list[ButtonCommand] = []
    panel = GpioButtonPanel(
        devices=devices,
        config=config,
        monotonic=clock,
        on_command=observed.append,
    )

    devices[PanelButton.SIMULACRO].press()
    clock.current = 14.9
    panel.poll()
    assert observed == []
    clock.current = 15.0
    panel.poll()
    assert observed == [ButtonCommand.START_SIMULACRO]
    clock.current = 20.0
    panel.poll()
    assert observed == [ButtonCommand.START_SIMULACRO]
    panel.close()


def test_missing_device_is_rejected_before_callbacks_are_bound() -> None:
    devices: dict[PanelButton, ButtonDevice] = {
        PanelButton.SIMULACRO: FakeButtonDevice(),
        PanelButton.STOP: FakeButtonDevice(),
    }

    with pytest.raises(ValueError, match="must contain"):
        GpioButtonPanel(
            devices=devices,
            config=DEFAULT_CONFIG.buttons,
            monotonic=FakeMonotonic(),
            on_command=lambda _command: None,
        )
