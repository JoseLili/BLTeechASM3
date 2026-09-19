"""Build compact OLED views from durable SAME notice receipts."""

from __future__ import annotations

from datetime import datetime, tzinfo

from asm.application.ports import SystemView
from asm.domain.same import SameEventCode, SameNoticeRecord
from asm.domain.states import SystemState


def collapse_repetitions(
    records: tuple[SameNoticeRecord, ...],
) -> tuple[SameNoticeRecord, ...]:
    """Keep only the newest receipt for each identical RF header."""
    observed: set[str] = set()
    collapsed: list[SameNoticeRecord] = []
    for record in records:
        if record.header.raw in observed:
            continue
        observed.add(record.header.raw)
        collapsed.append(record)
    return tuple(collapsed)


def recent_notice_view(
    record: SameNoticeRecord,
    *,
    index: int,
    total: int,
    timezone: tzinfo,
    now: datetime,
) -> SystemView:
    """Present one accepted event with local receipt time and history position."""
    if not 0 <= index < total:
        raise ValueError("index must reference one history record")
    local = record.received_at.astimezone(timezone)
    minutes = int(record.header.validity.total_seconds() // 60)
    active = record.expires_at > now
    state = (
        SystemState.EQW_ACTIVE
        if record.header.event is SameEventCode.EQW
        else SystemState.RWT_ACTIVE
    )
    return SystemView(
        state=state,
        title=f"{record.header.event.value} recibido",
        detail=local.strftime("%d/%m %H:%M"),
        footer=f"{'VIGENTE' if active else 'OK'} {index + 1}/{total} {minutes}m",
        compact=True,
    )


def empty_history_view() -> SystemView:
    """Describe an installation with no structured receipts yet."""
    return SystemView(
        state=SystemState.IDLE,
        title="Ultimos eventos",
        detail="Sin recepciones",
        footer="Esperando SAME",
    )
