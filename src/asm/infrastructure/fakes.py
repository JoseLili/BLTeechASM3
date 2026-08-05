"""Deterministic in-memory adapters for tests and PC simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from asm.application.ports import SystemView
from asm.domain.models import AuditRecord


@dataclass(slots=True)
class FakeClock:
    """Return deterministic timestamps and advance after each read."""

    current: datetime
    step: timedelta = timedelta(milliseconds=1)

    def now(self) -> datetime:
        value = self.current
        self.current += self.step
        return value


@dataclass(slots=True)
class InMemoryDisplay:
    """Capture rendered views in order."""

    history: list[SystemView] = field(default_factory=list)

    def show(self, view: SystemView) -> None:
        self.history.append(view)


@dataclass(slots=True)
class InMemoryEventLog:
    """Capture audit records in append-only order."""

    records: list[AuditRecord] = field(default_factory=list)

    def append(self, record: AuditRecord) -> None:
        self.records.append(record)
