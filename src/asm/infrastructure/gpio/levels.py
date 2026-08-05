"""Translate validated active-low button semantics for diagnostics."""

from __future__ import annotations


def active_low_level(*, is_active: bool) -> str:
    """Return the physical level expected from an active-low input."""
    return "LOW" if is_active else "HIGH"
