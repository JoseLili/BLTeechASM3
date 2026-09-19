from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from asm.application.same_history_presenter import (
    collapse_repetitions,
    empty_history_view,
    recent_notice_view,
)
from asm.domain.same import SameEndOfMessage, SameNoticeRecord, parse_multimon_same_line


def _record(raw: str, received_at: datetime) -> SameNoticeRecord:
    decoded = parse_multimon_same_line(raw)
    assert decoded is not None and not isinstance(decoded, SameEndOfMessage)
    return SameNoticeRecord(
        header=decoded,
        received_at=received_at,
        expires_at=received_at + decoded.validity,
    )


def test_repetitions_collapse_to_the_newest_identical_header() -> None:
    raw = "ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-"
    older = _record(raw, datetime(2026, 9, 19, 14, 45, tzinfo=UTC))
    newer = _record(raw, datetime(2026, 9, 19, 14, 46, tzinfo=UTC))

    assert collapse_repetitions((newer, older)) == (newer,)


def test_recent_view_shows_local_time_position_and_expired_status() -> None:
    record = _record(
        "ZCZC-CIV-EQW-000000+0005-832326-XDIF/005-",
        datetime(2026, 9, 19, 17, 52, tzinfo=UTC),
    )

    view = recent_notice_view(
        record,
        index=0,
        total=2,
        timezone=timezone(timedelta(hours=-6)),
        now=record.expires_at + timedelta(seconds=1),
    )

    assert view.title == "EQW recibido"
    assert view.detail == "19/09 11:52"
    assert view.footer == "OK 1/2 5m"


def test_empty_history_has_unambiguous_waiting_copy() -> None:
    view = empty_history_view()

    assert view.title == "Ultimos eventos"
    assert view.detail == "Sin recepciones"
