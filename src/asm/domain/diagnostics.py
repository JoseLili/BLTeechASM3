"""Immutable diagnostic evidence independent from operational transitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DiagnosticSeverity(StrEnum):
    """Presentation level without assigning an operational system state."""

    INFO = "INFO"
    WARNING = "WARNING"


@dataclass(frozen=True, slots=True)
class DiagnosticRecord:
    """One append-only hardware observation suitable for a JSONL log."""

    occurred_at: datetime
    component: str
    code: str
    severity: DiagnosticSeverity
    message: str
    context: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        for field_name, value in (
            ("component", self.component),
            ("code", self.code),
            ("message", self.message),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        keys = [key for key, _value in self.context]
        if len(keys) != len(set(keys)):
            raise ValueError("context keys must be unique")
