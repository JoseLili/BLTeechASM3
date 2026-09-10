from __future__ import annotations

from dataclasses import replace

import pytest

from asm.config import (
    DEFAULT_CONFIG,
    ActivationMode,
    BrandingConfig,
    ConfigurableButtonAction,
    DisplayConfig,
)


def test_factory_defaults_describe_current_brand_and_animation() -> None:
    assert DEFAULT_CONFIG.branding.company_name == "BLTeech"
    assert DEFAULT_CONFIG.branding.product_name == "ASM"
    assert DEFAULT_CONFIG.branding.generation == "v3"
    assert DEFAULT_CONFIG.display.startup_animation_seconds == 5.0
    assert DEFAULT_CONFIG.buttons.debounce_seconds == 0.05
    assert DEFAULT_CONFIG.buttons.simulacro.mode is ActivationMode.IMMEDIATE
    assert DEFAULT_CONFIG.buttons.evacuacion.mode is ActivationMode.IMMEDIATE
    assert DEFAULT_CONFIG.menu_buttons.debounce_seconds == 0.05
    assert DEFAULT_CONFIG.receiver.channel.value == "C7"
    assert DEFAULT_CONFIG.receiver.serial_device == "/dev/serial0"
    assert DEFAULT_CONFIG.receiver.command_timeout_seconds == 2.0
    assert DEFAULT_CONFIG.receiver.startup_settle_seconds == 1.0


@pytest.mark.parametrize(
    "field_name",
    ["company_name", "product_name", "generation", "startup_text"],
)
def test_branding_rejects_empty_required_text(field_name: str) -> None:
    values = {
        "company_name": "BLTeech",
        "product_name": "ASM",
        "generation": "v3",
        "startup_text": "Iniciando",
    }
    values[field_name] = " "

    with pytest.raises(ValueError, match=field_name):
        BrandingConfig(**values)


@pytest.mark.parametrize("seconds", [0, -1, 10.1])
def test_display_rejects_unsafe_animation_duration(seconds: float) -> None:
    with pytest.raises(ValueError, match="at most 10"):
        DisplayConfig(startup_animation_seconds=seconds)


@pytest.mark.parametrize("seconds", [0, -0.01, 0.201])
def test_buttons_reject_invalid_debounce(seconds: float) -> None:
    with pytest.raises(ValueError, match="at most 0.2"):
        replace(DEFAULT_CONFIG.buttons, debounce_seconds=seconds)


@pytest.mark.parametrize("seconds", [0, -0.01, 0.201])
def test_menu_buttons_reject_invalid_debounce(seconds: float) -> None:
    with pytest.raises(ValueError, match="at most 0.2"):
        replace(DEFAULT_CONFIG.menu_buttons, debounce_seconds=seconds)


@pytest.mark.parametrize("seconds", [0, -1, 10.1])
def test_receiver_rejects_invalid_command_timeout(seconds: float) -> None:
    with pytest.raises(ValueError, match="at most 10"):
        replace(DEFAULT_CONFIG.receiver, command_timeout_seconds=seconds)


@pytest.mark.parametrize("seconds", [-1, 10.1])
def test_receiver_rejects_invalid_startup_settle(seconds: float) -> None:
    with pytest.raises(ValueError, match="between zero and 10"):
        replace(DEFAULT_CONFIG.receiver, startup_settle_seconds=seconds)


@pytest.mark.parametrize("seconds", [0, -1, 10.1])
def test_configurable_actions_reject_invalid_hold_duration(seconds: float) -> None:
    with pytest.raises(ValueError, match="at most 10"):
        ConfigurableButtonAction(mode=ActivationMode.HOLD, hold_seconds=seconds)
