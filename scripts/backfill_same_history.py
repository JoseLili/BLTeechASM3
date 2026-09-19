"""Backfill structured SAME notice history from the diagnostic JSONL log."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import datetime, timedelta
from pathlib import Path

from asm.domain.same import SameEndOfMessage, SameNoticeRecord, parse_multimon_same_line
from asm.infrastructure.storage.same_notice_history import JsonLineSameNoticeRepository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostics", type=Path)
    parser.add_argument("history", type=Path)
    return parser


def backfill(diagnostics: Path, history: JsonLineSameNoticeRepository) -> int:
    """Append missing accepted headers and return the number imported."""
    existing = {
        (record.received_at.isoformat(), record.header.raw)
        for record in history.recent(limit=1_000_000)
    }
    imported = 0
    for line in diagnostics.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("code") != "SAME.HEADER.ACCEPTED":
            continue
        context = payload.get("context")
        occurred_at = payload.get("occurred_at")
        if not isinstance(context, dict) or not isinstance(occurred_at, str):
            continue
        raw = context.get("raw")
        validity_seconds = context.get("validity_seconds")
        if not isinstance(raw, str) or not isinstance(validity_seconds, str):
            continue
        decoded = parse_multimon_same_line(raw)
        if decoded is None or isinstance(decoded, SameEndOfMessage):
            continue
        received_at = datetime.fromisoformat(occurred_at)
        key = (received_at.isoformat(), decoded.raw)
        if key in existing:
            continue
        history.append(
            SameNoticeRecord(
                header=decoded,
                received_at=received_at,
                expires_at=received_at + timedelta(seconds=int(validity_seconds)),
            )
        )
        existing.add(key)
        imported += 1
    return imported


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    imported = backfill(args.diagnostics, JsonLineSameNoticeRepository(args.history))
    print(f"BACKFILL imported={imported} history={args.history}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
