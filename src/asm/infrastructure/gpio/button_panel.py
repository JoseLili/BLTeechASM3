"""GPIO adapter for the carrier's three active-low panel buttons.

Electrical details stop at this module. Application code receives semantic
``ButtonCommand`` values and never sees BCM numbers, pull-ups, or gpiozero.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from threading import Lock
from typing import Protocol, Self

from asm.application.button_policy import ButtonCommand, ButtonPolicyInterpreter, PanelButton
from asm.config.models import ButtonInputConfig


class ButtonDevice(Protocol):
    """Minimal gpiozero-compatible button surface required by the adapter."""

    when_pressed: Callable[[], None] | None
    when_released: Callable[[], None] | None

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ButtonPin:
    """Validated mapping between one semantic control and its BCM pin."""

    button: PanelButton
    gpio: int


BUTTON_PINS = (
    ButtonPin(PanelButton.SIMULACRO, 17),
    ButtonPin(PanelButton.STOP, 27),
    ButtonPin(PanelButton.EVACUACION, 22),
)


class GpioButtonPanel:
    """Translate debounced GPIO callbacks into configured semantic commands."""

    def __init__(
        self,
        *,
        devices: Mapping[PanelButton, ButtonDevice],
        config: ButtonInputConfig,
        monotonic: Callable[[], float],
        on_command: Callable[[ButtonCommand], None],
    ) -> None:
        expected = {pin.button for pin in BUTTON_PINS}
        if set(devices) != expected:
            raise ValueError("devices must contain Simulacro, Paro, and Evacuacion")

        self._devices = dict(devices)
        self._interpreter = ButtonPolicyInterpreter(config)
        self._monotonic = monotonic
        self._on_command = on_command
        self._policy_lock = Lock()

        for button, device in self._devices.items():
            # Default arguments bind the current loop value; without them every
            # callback would accidentally reference the last button.
            device.when_pressed = lambda button=button: self._pressed(button)
            device.when_released = lambda button=button: self._released(button)

    @classmethod
    def open(
        cls,
        *,
        config: ButtonInputConfig,
        monotonic: Callable[[], float],
        on_command: Callable[[ButtonCommand], None],
    ) -> Self:
        """Open validated BCM inputs using global Debian gpiozero support."""
        try:
            from gpiozero import Button  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError("GPIO support requires Debian package python3-gpiozero") from error

        devices = {
            pin.button: Button(
                pin=pin.gpio,
                pull_up=True,
                bounce_time=config.debounce_seconds,
            )
            for pin in BUTTON_PINS
        }
        return cls(
            devices=devices,
            config=config,
            monotonic=monotonic,
            on_command=on_command,
        )

    def poll(self) -> None:
        """Advance configurable HOLD policies without blocking the event loop."""
        with self._policy_lock:
            commands = self._interpreter.poll(occurred_at=self._monotonic())
        self._emit(commands)

    def close(self) -> None:
        """Release all GPIO resources and background callbacks."""
        for device in self._devices.values():
            device.close()

    def _pressed(self, button: PanelButton) -> None:
        with self._policy_lock:
            commands = self._interpreter.press(button, occurred_at=self._monotonic())
        self._emit(commands)

    def _released(self, button: PanelButton) -> None:
        with self._policy_lock:
            commands = self._interpreter.release(button, occurred_at=self._monotonic())
        self._emit(commands)

    def _emit(self, commands: tuple[ButtonCommand, ...]) -> None:
        for command in commands:
            self._on_command(command)
