"""Version-controlled factory defaults for ASM BLTeech v3."""

from __future__ import annotations

from asm.config.models import BrandingConfig, DisplayConfig, SystemConfig

DEFAULT_CONFIG = SystemConfig(
    branding=BrandingConfig(
        company_name="BLTeech",
        product_name="ASM",
        generation="v3",
        startup_text="Iniciando",
    ),
    display=DisplayConfig(startup_animation_seconds=5.0),
)
