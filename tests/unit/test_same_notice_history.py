from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from asm.domain.same import SameEndOfMessage, SameNoticeRecord, parse_multimon_same_line
from asm.infrastructure.storage.same_notice_history import (
    JsonLineSameNoticeRepository,
    SameNoticeHistoryError,
)


def _record(raw: str, received_at: datetime) -> SameNoticeRecord:
    decoded = parse_multimon_same_line(raw)
    assert decoded is not None and not isinstance(decoded, SameEndOfMessage)
    return SameNoticeRecord(
        header=decoded,
        received_at=received_at,
        expires_at=received_at + decoded.validity,
    )


def test_history_appends_and_returns_newest_receipts_first(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repository = JsonLineSameNoticeRepository(tmp_path / "notices.jsonl")
    first = _record(
        "ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-",
        datetime(2026, 9, 19, 14, 45, tzinfo=UTC),
    )
    second = _record(
        "ZCZC-CIV-EQW-000000+0005-832326-XDIF/005-",
        datetime(2026, 9, 19, 17, 52, tzinfo=UTC),
    )

    repository.append(first)
    repository.append(second)

    assert repository.recent(limit=1) == (second,)
    assert repository.recent(limit=10) == (second, first)


def test_missing_history_is_empty(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repository = JsonLineSameNoticeRepository(tmp_path / "missing.jsonl")

    assert repository.recent(limit=10) == ()


def test_corrupt_history_fails_explicitly(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "notices.jsonl"
    path.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(SameNoticeHistoryError):
        JsonLineSameNoticeRepository(path).recent(limit=10)


@pytest.mark.parametrize("limit", [0, -1])
def test_history_requires_positive_limit(tmp_path, limit: int) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        JsonLineSameNoticeRepository(tmp_path / "notices.jsonl").recent(limit=limit)


def test_notice_record_requires_aware_ordered_timestamps() -> None:
    decoded = parse_multimon_same_line("ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")
    assert decoded is not None and not isinstance(decoded, SameEndOfMessage)
    received_at = datetime(2026, 9, 19, tzinfo=UTC)

    with pytest.raises(ValueError):
        SameNoticeRecord(
            header=decoded,
            received_at=received_at,
            expires_at=received_at - timedelta(seconds=1),
        )
