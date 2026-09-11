from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity
from asm.infrastructure.storage.diagnostic_log import JsonLineDiagnosticLog


def test_diagnostic_log_appends_structured_durable_lines(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "diagnostics.jsonl"
    repository = JsonLineDiagnosticLog(path)
    record = DiagnosticRecord(
        occurred_at=datetime(2026, 9, 10, 12, 30, tzinfo=UTC),
        component="power",
        code="POWER.BATTERY_LOW.ASSERTED",
        severity=DiagnosticSeverity.INFO,
        message="Bateria baja: SI",
        context=(("signal", "BATTERY_LOW"), ("previous", "CLEAR")),
    )

    repository.append(record)
    repository.append(record)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    payload = json.loads(lines[0])
    assert payload["occurred_at"] == "2026-09-10T12:30:00+00:00"
    assert payload["code"] == "POWER.BATTERY_LOW.ASSERTED"
    assert payload["context"] == {"signal": "BATTERY_LOW", "previous": "CLEAR"}
