"""Non-blocking interpretation of debounced physical button gestures.

This module knows activation policies but not GPIO numbers or electrical
levels. It emits semantic commands that a later use case can map to domain
events after checking the current system state.
"""

from __future__ import annotations

from enum import StrEnum

from asm.config.models import ActivationMode, ButtonInputConfig, ConfigurableButtonAction


class PanelButton(StrEnum):
    """Physical controls identified after GPIO translation."""

    SIMULACRO = "SIMULACRO"
    STOP = "STOP"
    EVACUACION = "EVACUACION"


class ButtonCommand(StrEnum):
    """Semantic intent emitted at most once per physical gesture."""

    START_SIMULACRO = "START_SIMULACRO"
    STOP = "STOP"
    START_EVACUACION = "START_EVACUACION"


_COMMANDS = {
    PanelButton.SIMULACRO: ButtonCommand.START_SIMULACRO,
    PanelButton.STOP: ButtonCommand.STOP,
    PanelButton.EVACUACION: ButtonCommand.START_EVACUACION,
}


class ButtonPolicyInterpreter:
    """Convert press/release timing into non-repeating semantic commands."""

    def __init__(self, config: ButtonInputConfig) -> None:
        self._config = config
        self._pressed_at: dict[PanelButton, float] = {}
        self._emitted: set[PanelButton] = set()

    def press(self, button: PanelButton, *, occurred_at: float) -> tuple[ButtonCommand, ...]:
        """Register a debounced press and possibly emit an immediate command."""
        if button in self._pressed_at:
            # A held button cannot retrigger until a release closes its gesture.
            return ()
        self._pressed_at[button] = occurred_at

        if button is PanelButton.STOP or self._policy(button).mode is ActivationMode.IMMEDIATE:
            self._emitted.add(button)
            return (_COMMANDS[button],)
        return ()

    def release(self, button: PanelButton, *, occurred_at: float) -> tuple[ButtonCommand, ...]:
        """Close a gesture; releasing before a HOLD threshold cancels it."""
        started_at = self._pressed_at.get(button)
        if started_at is not None and occurred_at < started_at:
            raise ValueError("release time must not be earlier than press time")
        self._pressed_at.pop(button, None)
        self._emitted.discard(button)
        return ()

    def poll(self, *, occurred_at: float) -> tuple[ButtonCommand, ...]:
        """Emit completed HOLD gestures without sleeping or blocking the caller."""
        commands: list[ButtonCommand] = []
        for button, started_at in tuple(self._pressed_at.items()):
            if occurred_at < started_at:
                raise ValueError("poll time must not be earlier than press time")
            if button in self._emitted or button is PanelButton.STOP:
                continue
            policy = self._policy(button)
            hold_completed = occurred_at - started_at >= policy.hold_seconds
            if policy.mode is ActivationMode.HOLD and hold_completed:
                self._emitted.add(button)
                commands.append(_COMMANDS[button])
        return tuple(commands)

    def _policy(self, button: PanelButton) -> ConfigurableButtonAction:
        """Return policies only for the two actions allowed to be configurable."""
        if button is PanelButton.SIMULACRO:
            return self._config.simulacro
        if button is PanelButton.EVACUACION:
            return self._config.evacuacion
        raise ValueError("STOP activation policy is fixed and not configurable")
