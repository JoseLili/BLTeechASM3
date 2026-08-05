"""Technology-neutral ports used by application services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from asm.domain.models import AuditRecord
from asm.domain.states import SystemState


@dataclass(frozen=True, slots=True)
class SystemView:
    """Semantic content to present on a display."""

    state: SystemState
    title: str
    detail: str


class ClockPort(Protocol):
    """Provide civil time without coupling the application to the system clock."""

    def now(self) -> datetime: ...


class DisplayPort(Protocol):
    """Present semantic system information on any display adapter."""

    def show(self, view: SystemView) -> None: ...


class EventLogRepository(Protocol):
    """Persist audit records in append-only order."""

    def append(self, record: AuditRecord) -> None: ...
