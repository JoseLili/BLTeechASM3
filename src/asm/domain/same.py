"""Pure SAME/EAS message parsing and notice-validity tracking."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from asm.domain.indicators import IndicatorState


class SameEventCode(StrEnum):
    """SASMEX event codes supported by this product generation."""

    RWT = "RWT"
    EQW = "EQW"


@dataclass(frozen=True, slots=True)
class SameHeader:
    """Validated structure with non-authoritative sender/time metadata retained."""

    originator: str
    event: SameEventCode
    area_codes: tuple[str, ...]
    validity: timedelta
    issued_code: str
    sender: str
    raw: str

    @property
    def applies_to_all_units(self) -> bool:
        return "000000" in self.area_codes


@dataclass(frozen=True, slots=True)
class SameNoticeRecord:
    """Durable wall-clock receipt used to restore validity after a restart."""

    header: SameHeader
    received_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        for field_name, value in (
            ("received_at", self.received_at),
            ("expires_at", self.expires_at),
        ):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must be timezone-aware")
        if self.expires_at <= self.received_at:
            raise ValueError("expires_at must be later than received_at")


@dataclass(frozen=True, slots=True)
class SameEndOfMessage:
    """One decoded NNNN marker; it ends RF framing, not notice validity."""


class SameParseError(ValueError):
    """Raised when a ZCZC candidate cannot be safely interpreted."""


SameDecodedLine = SameHeader | SameEndOfMessage | None

_HEADER = re.compile(
    r"^ZCZC-"
    r"(?P<originator>[A-Z0-9]{3})-"
    r"(?P<event>[A-Z0-9]{3})-"
    r"(?P<areas>\d{6}(?:-\d{6})*)"
    r"\+(?P<duration>\d{4})-"
    r"(?P<issued>[^\s-]{1,16})-"
    r"(?P<sender>[^\s-]{8})-$"
)


def parse_multimon_same_line(line: str) -> SameDecodedLine:
    """Parse one multimon-ng line, ignoring unrelated diagnostic output."""
    payload = line.strip()
    if payload.startswith("EAS:"):
        payload = payload.removeprefix("EAS:").strip()
    if payload == "NNNN":
        return SameEndOfMessage()
    start = payload.find("ZCZC-")
    if start < 0:
        return None
    raw = payload[start:].split(maxsplit=1)[0]
    match = _HEADER.fullmatch(raw)
    if match is None:
        raise SameParseError("invalid SAME header structure")
    if match["originator"] != "CIV":
        raise SameParseError("unsupported SAME originator")
    try:
        event = SameEventCode(match["event"])
    except ValueError as error:
        raise SameParseError("unsupported SAME event") from error

    duration_code = match["duration"]
    hours = int(duration_code[:2])
    minutes = int(duration_code[2:])
    if minutes > 59 or (hours == 0 and minutes == 0):
        raise SameParseError("invalid SAME validity duration")

    return SameHeader(
        originator=match["originator"],
        event=event,
        area_codes=tuple(match["areas"].split("-")),
        validity=timedelta(hours=hours, minutes=minutes),
        issued_code=match["issued"],
        sender=match["sender"],
        raw=raw,
    )


class SameNoticeReceipt(StrEnum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True, slots=True)
class ActiveSameNotice:
    header: SameHeader
    received_at: float
    expires_at: float


@dataclass(frozen=True, slots=True)
class SameIndicatorSnapshot:
    """Observable result of the active SAME notice stack."""

    event: SameEventCode | None
    expires_in_seconds: float
    phase_on: bool
    indicators: IndicatorState


class SameNoticeTracker:
    """Deduplicate RF repetitions and derive the visible timed LED indication."""

    def __init__(
        self,
        *,
        blink_half_period_seconds: float,
        duplicate_window_seconds: float,
    ) -> None:
        if blink_half_period_seconds <= 0:
            raise ValueError("blink_half_period_seconds must be greater than zero")
        if duplicate_window_seconds <= 0:
            raise ValueError("duplicate_window_seconds must be greater than zero")
        self._blink_half_period_seconds = blink_half_period_seconds
        self._duplicate_window_seconds = duplicate_window_seconds
        self._active: dict[SameEventCode, ActiveSameNotice] = {}
        self._recent_headers: dict[str, float] = {}
        self._last_now: float | None = None

    def receive(self, header: SameHeader, *, received_at: float) -> SameNoticeReceipt:
        self._check_monotonic(received_at)
        self._purge_recent(received_at)
        previous = self._recent_headers.get(header.raw)
        if previous is not None and received_at - previous <= self._duplicate_window_seconds:
            return SameNoticeReceipt.DUPLICATE

        self._recent_headers[header.raw] = received_at
        validity_seconds = header.validity.total_seconds()
        self._active[header.event] = ActiveSameNotice(
            header=header,
            received_at=received_at,
            expires_at=received_at + validity_seconds,
        )
        return SameNoticeReceipt.ACCEPTED

    def snapshot(self, *, now: float) -> SameIndicatorSnapshot:
        self._check_monotonic(now)
        self._active = {
            event: notice
            for event, notice in self._active.items()
            if notice.expires_at > now
        }
        if not self._active:
            return SameIndicatorSnapshot(
                event=None,
                expires_in_seconds=0.0,
                phase_on=False,
                indicators=IndicatorState(power=True),
            )

        event = max(self._active, key=_same_event_priority)
        notice = self._active[event]
        phase_index = int(
            (now - notice.received_at) // self._blink_half_period_seconds
        )
        phase_on = phase_index % 2 == 0
        return SameIndicatorSnapshot(
            event=event,
            expires_in_seconds=notice.expires_at - now,
            phase_on=phase_on,
            indicators=IndicatorState(
                advisory=event is SameEventCode.RWT and phase_on,
                warning=event is SameEventCode.EQW and phase_on,
                power=True,
            ),
        )

    def _check_monotonic(self, now: float) -> None:
        if self._last_now is not None and now < self._last_now:
            raise ValueError("monotonic time must not move backwards")
        self._last_now = now

    def _purge_recent(self, now: float) -> None:
        self._recent_headers = {
            raw: seen_at
            for raw, seen_at in self._recent_headers.items()
            if now - seen_at <= self._duplicate_window_seconds
        }


def _same_event_priority(event: SameEventCode) -> int:
    return {SameEventCode.RWT: 10, SameEventCode.EQW: 40}[event]
