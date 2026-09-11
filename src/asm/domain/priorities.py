"""Pure priority catalog for operational alert events and states."""

from __future__ import annotations

from enum import IntEnum

from asm.domain.states import EventType, SystemState


class EventPriority(IntEnum):
    """Increasing operational urgency; STOP is intentionally not included."""

    RWT = 10
    SIMULACRO = 20
    EVACUACION = 30
    EQW = 40


START_EVENT_STATES: dict[EventType, SystemState] = {
    EventType.START_RWT: SystemState.RWT_ACTIVE,
    EventType.START_SIMULACRO: SystemState.SIMULACRO_ACTIVE,
    EventType.START_EVACUACION: SystemState.EVACUACION_ACTIVE,
    EventType.START_EQW: SystemState.EQW_ACTIVE,
}

EVENT_PRIORITIES: dict[EventType, EventPriority] = {
    EventType.START_RWT: EventPriority.RWT,
    EventType.START_SIMULACRO: EventPriority.SIMULACRO,
    EventType.START_EVACUACION: EventPriority.EVACUACION,
    EventType.START_EQW: EventPriority.EQW,
}

STATE_PRIORITIES: dict[SystemState, EventPriority] = {
    SystemState.RWT_ACTIVE: EventPriority.RWT,
    SystemState.SIMULACRO_ACTIVE: EventPriority.SIMULACRO,
    SystemState.EVACUACION_ACTIVE: EventPriority.EVACUACION,
    SystemState.EQW_ACTIVE: EventPriority.EQW,
}
