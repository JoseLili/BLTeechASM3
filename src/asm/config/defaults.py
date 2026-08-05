"""Version-controlled factory defaults for ASM BLTeech v3."""

from __future__ import annotations

from asm.config.models import (
    ActivationMode,
    BrandingConfig,
    ButtonInputConfig,
    ConfigurableButtonAction,
    DisplayConfig,
    SystemConfig,
)

DEFAULT_CONFIG = SystemConfig(
    branding=BrandingConfig(
        company_name="BLTeech",
        product_name="ASM",
        generation="v3",
        startup_text="Iniciando",
    ),
    display=DisplayConfig(startup_animation_seconds=5.0),
    buttons=ButtonInputConfig(
        debounce_seconds=0.05,
        simulacro=ConfigurableButtonAction(
            mode=ActivationMode.IMMEDIATE,
            hold_seconds=5.0,
        ),
        evacuacion=ConfigurableButtonAction(
            mode=ActivationMode.IMMEDIATE,
            hold_seconds=5.0,
        ),
    ),
)
