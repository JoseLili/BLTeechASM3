"""Console adapters for the hardware-free executable demonstration."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from typing import TextIO

from asm.application.ports import SystemView
from asm.domain.models import AuditRecord


class SystemClock:
    """Production-independent wall clock adapter."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class ConsoleDisplay:
    """Render the semantic OLED view as one console line."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream

    def show(self, view: SystemView) -> None:
        print(f"[DISPLAY] {view.state}: {view.title} — {view.detail}", file=self._stream)


class JsonLineEventLog:
    """Write structured audit records as JSON lines."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream

    def append(self, record: AuditRecord) -> None:
        print(json.dumps(asdict(record), default=str, ensure_ascii=False), file=self._stream)
