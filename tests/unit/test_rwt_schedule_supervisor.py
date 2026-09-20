from __future__ import annotations

from datetime import datetime, timedelta, timezone

from asm.application.rwt_schedule_supervisor import (
    RwtScheduleState,
    RwtScheduleSupervisor,
)
from asm.domain.same import SameHeader, SameNoticeRecord, parse_multimon_same_line
from asm.infrastructure.fakes import FakeClock, InMemoryDiagnosticLog

LOCAL = timezone(timedelta(hours=-6))


def _record(received_at: datetime, event: str = "RWT") -> SameNoticeRecord:
    decoded = parse_multimon_same_line(
        f"EAS: ZCZC-CIV-{event}-000000+0300-832300-XDIF/005-"
    )
    assert isinstance(decoded, SameHeader)
    return SameNoticeRecord(
        header=decoded,
        received_at=received_at,
        expires_at=received_at + decoded.validity,
    )


def _supervisor(now: datetime) -> tuple[RwtScheduleSupervisor, InMemoryDiagnosticLog]:
    log = InMemoryDiagnosticLog()
    supervisor = RwtScheduleSupervisor(
        clock=FakeClock(now, step=timedelta(0)),
        diagnostic_log=log,
        operator_timezone=LOCAL,
    )
    return supervisor, log


def test_early_1737_receipt_satisfies_1745_slot() -> None:
    supervisor, log = _supervisor(datetime(2026, 9, 19, 17, 37, tzinfo=LOCAL))

    transition = supervisor.observe(_record(datetime(2026, 9, 19, 17, 37, tzinfo=LOCAL)))

    assert transition is not None
    assert transition.state is RwtScheduleState.RECEIVED
    assert transition.expected_at == datetime(2026, 9, 19, 17, 45, tzinfo=LOCAL)
    assert log.records[-1].code == "RWT.SCHEDULE.RECEIVED"


def test_missing_window_is_reported_only_after_late_tolerance() -> None:
    before_close, early_log = _supervisor(datetime(2026, 9, 19, 20, 59, tzinfo=LOCAL))
    before_close.restore((_record(datetime(2026, 9, 19, 17, 37, tzinfo=LOCAL)),))
    assert before_close.poll() is None
    assert early_log.records == []

    after_close, late_log = _supervisor(datetime(2026, 9, 19, 21, 0, tzinfo=LOCAL))
    after_close.restore((_record(datetime(2026, 9, 19, 17, 37, tzinfo=LOCAL)),))

    transition = after_close.poll()

    assert transition is not None
    assert transition.state is RwtScheduleState.MISSED
    assert transition.expected_at == datetime(2026, 9, 19, 20, 45, tzinfo=LOCAL)
    assert late_log.records[-1].code == "RWT.SCHEDULE.MISSED"
    assert after_close.poll() is None
    assert len(late_log.records) == 1


def test_restore_marks_closed_slot_healthy_without_relogging_it() -> None:
    supervisor, log = _supervisor(datetime(2026, 9, 19, 18, 1, tzinfo=LOCAL))
    supervisor.restore((_record(datetime(2026, 9, 19, 17, 37, tzinfo=LOCAL)),))

    assert supervisor.poll() is None
    assert supervisor.status.state is RwtScheduleState.RECEIVED
    assert supervisor.status.received_at == datetime(2026, 9, 19, 17, 37, tzinfo=LOCAL)
    assert log.records == []


def test_eqw_does_not_satisfy_rwt_schedule() -> None:
    supervisor, _log = _supervisor(datetime(2026, 9, 19, 18, 1, tzinfo=LOCAL))

    assert supervisor.observe(
        _record(datetime(2026, 9, 19, 17, 45, tzinfo=LOCAL), event="EQW")
    ) is None
    assert supervisor.status.state is RwtScheduleState.UNKNOWN


def test_next_slot_rolls_over_midnight() -> None:
    supervisor, _log = _supervisor(datetime(2026, 9, 19, 23, 50, tzinfo=LOCAL))

    assert supervisor.status.next_expected_at == datetime(
        2026, 9, 20, 2, 45, tzinfo=LOCAL
    )


def test_notice_validity_is_not_changed_by_schedule_matching() -> None:
    supervisor, _log = _supervisor(datetime(2026, 9, 19, 17, 37, tzinfo=LOCAL))
    record = _record(datetime(2026, 9, 19, 17, 37, tzinfo=LOCAL))

    supervisor.observe(record)

    assert record.expires_at == datetime(2026, 9, 19, 20, 37, tzinfo=LOCAL)
