from __future__ import annotations

import pytest

from asm.config import DEFAULT_CONFIG, BrandingConfig, DisplayConfig


def test_factory_defaults_describe_current_brand_and_animation() -> None:
    assert DEFAULT_CONFIG.branding.company_name == "BLTeech"
    assert DEFAULT_CONFIG.branding.product_name == "ASM"
    assert DEFAULT_CONFIG.branding.generation == "v3"
    assert DEFAULT_CONFIG.display.startup_animation_seconds == 5.0


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
