"""Durable append-only JSONL storage for operational decisions."""

from __future__ import annotations

import json
import os
from pathlib import Path

from asm.domain.models import AuditRecord


class JsonLineAuditLog:
    """Append and fsync every accepted or rejected state-machine decision."""

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser()

    def append(self, record: AuditRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "occurred_at": record.occurred_at.isoformat(),
            "event": record.event.value,
            "source": record.source.value,
            "previous_state": record.previous_state.value,
            "resulting_state": (
                record.resulting_state.value if record.resulting_state is not None else None
            ),
            "accepted": record.accepted,
            "reason": record.reason,
        }
        encoded = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        descriptor = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o640)
        try:
            written = os.write(descriptor, encoded)
            if written != len(encoded):
                raise OSError("incomplete audit log write")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
