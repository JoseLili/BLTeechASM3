from __future__ import annotations

from datetime import UTC, datetime

import pytest

from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity


def _record(**changes: object) -> DiagnosticRecord:
    values: dict[str, object] = {
        "occurred_at": datetime(2026, 9, 10, tzinfo=UTC),
        "component": "power",
        "code": "POWER.AC_OK.CLEAR",
        "severity": DiagnosticSeverity.INFO,
        "message": "Red CA disponible: NO",
        "context": (("signal", "AC_OK"),),
    }
    values.update(changes)
    return DiagnosticRecord(**values)  # type: ignore[arg-type]


def test_diagnostic_record_requires_aware_time_and_unique_context() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _record(occurred_at=datetime(2026, 9, 10))
    with pytest.raises(ValueError, match="unique"):
        _record(context=(("signal", "AC_OK"), ("signal", "AC_OK")))


@pytest.mark.parametrize("field", ["component", "code", "message"])
def test_diagnostic_record_requires_text(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        _record(**{field: " "})
