from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from asm.domain.models import AuditRecord
from asm.domain.states import EventSource, EventType, SystemState
from asm.infrastructure.storage.audit_log import JsonLineAuditLog


def test_audit_log_appends_accepted_and_rejected_decisions(tmp_path: Path) -> None:
    path = tmp_path / "state" / "audit.jsonl"
    repository = JsonLineAuditLog(path)
    accepted = AuditRecord(
        occurred_at=datetime(2026, 9, 10, 12, 30, tzinfo=UTC),
        event=EventType.START_EVACUACION,
        source=EventSource.LOCAL_PANEL,
        previous_state=SystemState.IDLE,
        resulting_state=SystemState.EVACUACION_ACTIVE,
        accepted=True,
        reason="transition accepted",
    )
    rejected = AuditRecord(
        occurred_at=datetime(2026, 9, 10, 12, 31, tzinfo=UTC),
        event=EventType.STOP_REQUESTED,
        source=EventSource.LOCAL_PANEL,
        previous_state=SystemState.EQW_ACTIVE,
        resulting_state=None,
        accepted=False,
        reason="invalid transition",
    )

    repository.append(accepted)
    repository.append(rejected)

    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert records[0]["source"] == "LOCAL_PANEL"
    assert records[0]["resulting_state"] == "EVACUACION_ACTIVE"
    assert records[1]["accepted"] is False
    assert records[1]["resulting_state"] is None
