from __future__ import annotations

from dataclasses import replace

import pytest

from asm.application.button_policy import ButtonCommand, ButtonPolicyInterpreter, PanelButton
from asm.config import DEFAULT_CONFIG, ActivationMode, ConfigurableButtonAction


def _hold_config(*, seconds: float = 5.0):
    hold = ConfigurableButtonAction(mode=ActivationMode.HOLD, hold_seconds=seconds)
    return replace(DEFAULT_CONFIG.buttons, simulacro=hold, evacuacion=hold)


@pytest.mark.parametrize(
    ("button", "expected"),
    [
        (PanelButton.SIMULACRO, ButtonCommand.START_SIMULACRO),
        (PanelButton.STOP, ButtonCommand.STOP),
        (PanelButton.EVACUACION, ButtonCommand.START_EVACUACION),
    ],
)
def test_factory_defaults_emit_every_button_immediately(
    button: PanelButton,
    expected: ButtonCommand,
) -> None:
    interpreter = ButtonPolicyInterpreter(DEFAULT_CONFIG.buttons)

    assert interpreter.press(button, occurred_at=1.0) == (expected,)


def test_held_immediate_button_does_not_repeat_until_release() -> None:
    interpreter = ButtonPolicyInterpreter(DEFAULT_CONFIG.buttons)

    assert interpreter.press(PanelButton.STOP, occurred_at=1.0) == (ButtonCommand.STOP,)
    assert interpreter.press(PanelButton.STOP, occurred_at=2.0) == ()
    assert interpreter.poll(occurred_at=10.0) == ()
    assert interpreter.release(PanelButton.STOP, occurred_at=10.1) == ()
    assert interpreter.press(PanelButton.STOP, occurred_at=11.0) == (ButtonCommand.STOP,)


def test_hold_released_before_threshold_is_cancelled() -> None:
    interpreter = ButtonPolicyInterpreter(_hold_config())

    assert interpreter.press(PanelButton.SIMULACRO, occurred_at=10.0) == ()
    assert interpreter.poll(occurred_at=14.9) == ()
    assert interpreter.release(PanelButton.SIMULACRO, occurred_at=14.9) == ()
    assert interpreter.poll(occurred_at=20.0) == ()


def test_hold_emits_once_at_threshold_and_waits_for_release() -> None:
    interpreter = ButtonPolicyInterpreter(_hold_config())

    interpreter.press(PanelButton.EVACUACION, occurred_at=10.0)

    assert interpreter.poll(occurred_at=15.0) == (ButtonCommand.START_EVACUACION,)
    assert interpreter.poll(occurred_at=30.0) == ()


def test_stop_remains_immediate_when_other_buttons_use_hold() -> None:
    interpreter = ButtonPolicyInterpreter(_hold_config(seconds=10.0))

    assert interpreter.press(PanelButton.STOP, occurred_at=1.0) == (ButtonCommand.STOP,)


def test_monotonic_timestamps_cannot_move_backwards() -> None:
    interpreter = ButtonPolicyInterpreter(_hold_config())
    interpreter.press(PanelButton.SIMULACRO, occurred_at=10.0)

    with pytest.raises(ValueError, match="earlier"):
        interpreter.poll(occurred_at=9.0)
    with pytest.raises(ValueError, match="earlier"):
        interpreter.release(PanelButton.SIMULACRO, occurred_at=9.0)
