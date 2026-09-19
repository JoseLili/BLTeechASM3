from __future__ import annotations

from asm.domain.priorities import EVENT_PRIORITIES, EventPriority
from asm.domain.states import EventType


def test_operational_priority_order_is_explicit() -> None:
    assert list(EventPriority) == [
        EventPriority.RWT,
        EventPriority.SIMULACRO,
        EventPriority.EVACUACION,
        EventPriority.EQW,
    ]
    assert EVENT_PRIORITIES == {
        EventType.START_RWT: EventPriority.RWT,
        EventType.START_SIMULACRO: EventPriority.SIMULACRO,
        EventType.START_EVACUACION: EventPriority.EVACUACION,
        EventType.START_EQW: EventPriority.EQW,
    }
