"""Typed and immutable application configuration models.

Configuration holds installation and presentation choices. Safety rules such
as event priorities and valid state transitions deliberately do not belong
here, because they must not change through an operator-edited file.
"""

from __future__ import annotations

from dataclasses import dataclass


def _required_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class BrandingConfig:
    """Names and labels used to identify BLTeech and this product generation."""

    company_name: str
    product_name: str
    generation: str
    startup_text: str

    def __post_init__(self) -> None:
        _required_text(self.company_name, "company_name")
        _required_text(self.product_name, "product_name")
        _required_text(self.generation, "generation")
        _required_text(self.startup_text, "startup_text")


@dataclass(frozen=True, slots=True)
class DisplayConfig:
    """Non-critical timing choices for the local display."""

    startup_animation_seconds: float

    def __post_init__(self) -> None:
        if not 0 < self.startup_animation_seconds <= 10:
            raise ValueError("startup_animation_seconds must be greater than zero and at most 10")


@dataclass(frozen=True, slots=True)
class SystemConfig:
    """Root object passed explicitly to application composition code."""

    branding: BrandingConfig
    display: DisplayConfig
