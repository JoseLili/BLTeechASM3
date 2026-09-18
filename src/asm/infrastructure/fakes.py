"""Deterministic in-memory adapters for tests and PC simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from asm.application.ports import DiagnosticView, SystemView
from asm.domain.diagnostics import DiagnosticRecord
from asm.domain.indicators import IndicatorState
from asm.domain.models import AuditRecord
from asm.domain.states import EventType


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
    diagnostics: list[DiagnosticView] = field(default_factory=list)

    def show(self, view: SystemView) -> None:
        self.history.append(view)

    def show_diagnostic(self, view: DiagnosticView) -> None:
        self.diagnostics.append(view)


@dataclass(slots=True)
class InMemoryEventLog:
    """Capture audit records in append-only order."""

    records: list[AuditRecord] = field(default_factory=list)

    def append(self, record: AuditRecord) -> None:
        self.records.append(record)


@dataclass(slots=True)
class InMemoryDiagnosticLog:
    """Capture hardware diagnostic records in append-only order."""

    records: list[DiagnosticRecord] = field(default_factory=list)

    def append(self, record: DiagnosticRecord) -> None:
        self.records.append(record)


@dataclass(slots=True)
class InMemoryIndicatorPanel:
    """Capture complete panel states in order."""

    history: list[IndicatorState] = field(default_factory=list)

    def apply(self, state: IndicatorState) -> None:
        self.history.append(state)


@dataclass(slots=True)
class InMemoryEventAudio:
    """Capture requested event audio without opening ALSA."""

    played: list[EventType] = field(default_factory=list)
    stop_calls: int = 0

    def play(self, event: EventType) -> bool:
        self.played.append(event)
        return True

    def poll(self) -> None:
        return

    def stop(self) -> None:
        self.stop_calls += 1
