"""Durable append-only JSONL storage for hardware diagnostics."""

from __future__ import annotations

import json
import os
from pathlib import Path

from asm.domain.diagnostics import DiagnosticRecord


class JsonLineDiagnosticLog:
    """Append and fsync every diagnostic record to survive abrupt power loss."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: DiagnosticRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "occurred_at": record.occurred_at.isoformat(),
            "component": record.component,
            "code": record.code,
            "severity": record.severity.value,
            "message": record.message,
            "context": dict(record.context),
        }
        encoded = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        descriptor = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o640)
        try:
            written = os.write(descriptor, encoded)
            if written != len(encoded):
                raise OSError("incomplete diagnostic log write")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
