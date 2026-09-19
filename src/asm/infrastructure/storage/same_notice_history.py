"""Append-only JSONL history for accepted SAME notices."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from asm.domain.same import (
    SameEndOfMessage,
    SameNoticeRecord,
    parse_multimon_same_line,
)


class SameNoticeHistoryError(RuntimeError):
    """Raised when durable SAME history cannot be read or appended safely."""


class JsonLineSameNoticeRepository:
    """Store one fsynced JSON object per accepted SAME header."""

    SCHEMA_VERSION = 1

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser()

    def append(self, record: SameNoticeRecord) -> None:
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "received_at": record.received_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "raw": record.header.raw,
        }
        encoded = (
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(
                self.path,
                os.O_APPEND | os.O_CREAT | os.O_WRONLY,
                0o640,
            )
            try:
                written = os.write(descriptor, encoded)
                if written != len(encoded):
                    raise OSError("incomplete SAME history write")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as error:
            raise SameNoticeHistoryError(
                f"could not append SAME history: {self.path}"
            ) from error

    def recent(self, *, limit: int) -> tuple[SameNoticeRecord, ...]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        if not self.path.exists():
            return ()
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
            records = tuple(self._decode(line) for line in lines if line.strip())
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            raise SameNoticeHistoryError(
                f"invalid SAME history: {self.path}"
            ) from error
        return tuple(reversed(records[-limit:]))

    def _decode(self, line: str) -> SameNoticeRecord:
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError("history record must be an object")
        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("unsupported schema_version")
        raw = payload.get("raw")
        received_at = payload.get("received_at")
        expires_at = payload.get("expires_at")
        if not all(isinstance(value, str) for value in (raw, received_at, expires_at)):
            raise ValueError("history fields must be text")
        decoded = parse_multimon_same_line(raw)
        if decoded is None or isinstance(decoded, SameEndOfMessage):
            raise ValueError("history raw value must be a SAME header")
        return SameNoticeRecord(
            header=decoded,
            received_at=datetime.fromisoformat(received_at),
            expires_at=datetime.fromisoformat(expires_at),
        )
