"""Pure domain records used by the initial application flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from asm.domain.states import EventSource, EventType, SystemState


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Immutable evidence of an accepted or rejected state transition."""

    occurred_at: datetime
    event: EventType
    source: EventSource
    previous_state: SystemState
    resulting_state: SystemState | None
    accepted: bool
    reason: str

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        if self.accepted != (self.resulting_state is not None):
            raise ValueError("accepted and resulting_state must agree")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class StateTransition:
    """Result of applying one valid event to a system state."""

    event: EventType
    previous_state: SystemState
    resulting_state: SystemState
