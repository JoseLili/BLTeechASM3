"""Supervise the expected three-hourly RWT reception schedule."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo
from enum import StrEnum

from asm.application.ports import ClockPort, DiagnosticLogRepository
from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity
from asm.domain.same import SameEventCode, SameNoticeRecord

_EXPECTED_HOURS = (2, 5, 8, 11, 14, 17, 20, 23)


class RwtScheduleState(StrEnum):
    """Health of the newest expected RWT slot known to the supervisor."""

    UNKNOWN = "UNKNOWN"
    RECEIVED = "RECEIVED"
    MISSED = "MISSED"


@dataclass(frozen=True, slots=True)
class RwtScheduleStatus:
    """Operator-facing schedule status independent from SAME validity."""

    state: RwtScheduleState
    expected_at: datetime | None
    received_at: datetime | None
    next_expected_at: datetime


@dataclass(frozen=True, slots=True)
class RwtScheduleTransition:
    """One newly determined schedule outcome."""

    state: RwtScheduleState
    expected_at: datetime
    received_at: datetime | None
    current_status: RwtScheduleStatus


class RwtScheduleSupervisor:
    """Audit RWT receipts against local slots without changing notice validity."""

    def __init__(
        self,
        *,
        clock: ClockPort,
        diagnostic_log: DiagnosticLogRepository,
        operator_timezone: tzinfo,
        early_tolerance: timedelta = timedelta(minutes=15),
        late_tolerance: timedelta = timedelta(minutes=15),
    ) -> None:
        if early_tolerance < timedelta(0):
            raise ValueError("early_tolerance must not be negative")
        if late_tolerance < timedelta(0):
            raise ValueError("late_tolerance must not be negative")
        self._clock = clock
        self._diagnostic_log = diagnostic_log
        self._timezone = operator_timezone
        self._early_tolerance = early_tolerance
        self._late_tolerance = late_tolerance
        self._outcomes: dict[datetime, datetime | None] = {}

    @property
    def status(self) -> RwtScheduleStatus:
        """Return the newest known outcome and the next nominal slot."""
        now = self._local(self._clock.now())
        if not self._outcomes:
            return RwtScheduleStatus(
                state=RwtScheduleState.UNKNOWN,
                expected_at=None,
                received_at=None,
                next_expected_at=_next_slot(now),
            )
        expected_at = max(self._outcomes)
        received_at = self._outcomes[expected_at]
        return RwtScheduleStatus(
            state=(
                RwtScheduleState.RECEIVED
                if received_at is not None
                else RwtScheduleState.MISSED
            ),
            expected_at=expected_at,
            received_at=received_at,
            next_expected_at=_next_slot(now),
        )

    def restore(self, records: tuple[SameNoticeRecord, ...]) -> None:
        """Load prior receipts without generating new diagnostic records."""
        for record in sorted(records, key=lambda item: item.received_at):
            self._remember(record)

    def observe(self, record: SameNoticeRecord) -> RwtScheduleTransition | None:
        """Accept one live receipt and publish its matching scheduled slot."""
        expected_at = self._remember(record)
        if expected_at is None:
            return None
        received_at = self._outcomes[expected_at]
        transition = RwtScheduleTransition(
            state=RwtScheduleState.RECEIVED,
            expected_at=expected_at,
            received_at=received_at,
            current_status=self.status,
        )
        self._append(transition)
        return transition

    def poll(self) -> RwtScheduleTransition | None:
        """Declare the latest closed window received or missed exactly once."""
        now = self._local(self._clock.now())
        expected_at = _latest_closed_slot(now, self._late_tolerance)
        if expected_at in self._outcomes:
            return None
        self._outcomes[expected_at] = None
        transition = RwtScheduleTransition(
            state=RwtScheduleState.MISSED,
            expected_at=expected_at,
            received_at=None,
            current_status=self.status,
        )
        self._append(transition)
        return transition

    def _remember(self, record: SameNoticeRecord) -> datetime | None:
        if record.header.event is not SameEventCode.RWT:
            return None
        received_at = self._local(record.received_at)
        expected_at = _matching_slot(
            received_at,
            early_tolerance=self._early_tolerance,
            late_tolerance=self._late_tolerance,
        )
        if expected_at is None or expected_at in self._outcomes:
            return None
        self._outcomes[expected_at] = received_at
        return expected_at

    def _local(self, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("schedule timestamps must be timezone-aware")
        return value.astimezone(self._timezone)

    def _append(self, transition: RwtScheduleTransition) -> None:
        received = transition.received_at
        self._diagnostic_log.append(
            DiagnosticRecord(
                occurred_at=self._clock.now(),
                component="rwt_schedule",
                code=f"RWT.SCHEDULE.{transition.state.value}",
                severity=(
                    DiagnosticSeverity.INFO
                    if transition.state is RwtScheduleState.RECEIVED
                    else DiagnosticSeverity.WARNING
                ),
                message=(
                    "RWT recibida dentro de la ventana programada"
                    if transition.state is RwtScheduleState.RECEIVED
                    else "No se recibio una RWT completa en la ventana programada"
                ),
                context=(
                    ("expected_local", transition.expected_at.isoformat()),
                    ("received_local", received.isoformat() if received else "NONE"),
                    ("early_tolerance_minutes", _minutes(self._early_tolerance)),
                    ("late_tolerance_minutes", _minutes(self._late_tolerance)),
                ),
            )
        )


def _matching_slot(
    received_at: datetime,
    *,
    early_tolerance: timedelta,
    late_tolerance: timedelta,
) -> datetime | None:
    days = (
        received_at.date() - timedelta(days=1),
        received_at.date(),
        received_at.date() + timedelta(days=1),
    )
    candidates = _slots_for_dates(days, received_at.tzinfo)
    matches = (
        slot
        for slot in candidates
        if slot - early_tolerance <= received_at <= slot + late_tolerance
    )
    return min(matches, key=lambda slot: abs(slot - received_at), default=None)


def _latest_closed_slot(now: datetime, late_tolerance: timedelta) -> datetime:
    days = (now.date() - timedelta(days=1), now.date())
    candidates = _slots_for_dates(days, now.tzinfo)
    return max(slot for slot in candidates if slot + late_tolerance <= now)


def _next_slot(now: datetime) -> datetime:
    days = (now.date(), now.date() + timedelta(days=1))
    candidates = _slots_for_dates(days, now.tzinfo)
    return min(slot for slot in candidates if slot > now)


def _slots_for_dates(days: tuple[date, ...], timezone: tzinfo | None) -> tuple[datetime, ...]:
    return tuple(
        datetime.combine(day, time(hour=hour, minute=45), tzinfo=timezone)
        for day in days
        for hour in _EXPECTED_HOURS
    )


def _minutes(value: timedelta) -> str:
    return str(int(value.total_seconds() // 60))
