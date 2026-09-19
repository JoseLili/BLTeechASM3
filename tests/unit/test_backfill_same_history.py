from __future__ import annotations

import json

from asm.infrastructure.storage.same_notice_history import JsonLineSameNoticeRepository
from scripts.backfill_same_history import backfill


def test_backfill_imports_accepted_headers_once(tmp_path) -> None:  # type: ignore[no-untyped-def]
    diagnostics = tmp_path / "diagnostics.jsonl"
    accepted = {
        "occurred_at": "2026-09-19T17:52:04.294206+00:00",
        "code": "SAME.HEADER.ACCEPTED",
        "context": {
            "raw": "ZCZC-CIV-EQW-000000+0005-832326-XDIF/005-",
            "validity_seconds": "300",
        },
    }
    ignored = {"occurred_at": "2026-09-19T17:52:07+00:00", "code": "SAME.END"}
    diagnostics.write_text(
        "\n".join((json.dumps(accepted), json.dumps(ignored))) + "\n",
        encoding="utf-8",
    )
    history = JsonLineSameNoticeRepository(tmp_path / "notices.jsonl")

    assert backfill(diagnostics, history) == 1
    assert backfill(diagnostics, history) == 0

    records = history.recent(limit=10)
    assert len(records) == 1
    assert records[0].header.event.value == "EQW"
    assert (records[0].expires_at - records[0].received_at).total_seconds() == 300
