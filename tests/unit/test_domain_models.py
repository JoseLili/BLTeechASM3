from __future__ import annotations

from datetime import UTC, datetime

import pytest

from asm.domain.models import AuditRecord
from asm.domain.states import EventType, SystemState


def test_audit_record_accepts_aware_timestamp() -> None:
    record = AuditRecord(
        occurred_at=datetime(2026, 8, 5, tzinfo=UTC),
        event=EventType.BOOT_COMPLETED,
        previous_state=SystemState.BOOT,
        resulting_state=SystemState.SELF_TEST,
        accepted=True,
        reason="transition accepted",
    )

    assert record.accepted is True


def test_audit_record_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        AuditRecord(
            occurred_at=datetime(2026, 8, 5),
            event=EventType.BOOT_COMPLETED,
            previous_state=SystemState.BOOT,
            resulting_state=SystemState.SELF_TEST,
            accepted=True,
            reason="transition accepted",
        )


@pytest.mark.parametrize(
    ("accepted", "resulting_state"),
    [(True, None), (False, SystemState.SELF_TEST)],
)
def test_audit_record_requires_consistent_result(
    accepted: bool,
    resulting_state: SystemState | None,
) -> None:
    with pytest.raises(ValueError, match="must agree"):
        AuditRecord(
            occurred_at=datetime(2026, 8, 5, tzinfo=UTC),
            event=EventType.BOOT_COMPLETED,
            previous_state=SystemState.BOOT,
            resulting_state=resulting_state,
            accepted=accepted,
            reason="test",
        )


def test_audit_record_rejects_empty_reason() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        AuditRecord(
            occurred_at=datetime(2026, 8, 5, tzinfo=UTC),
            event=EventType.BOOT_COMPLETED,
            previous_state=SystemState.BOOT,
            resulting_state=SystemState.SELF_TEST,
            accepted=True,
            reason=" ",
        )
