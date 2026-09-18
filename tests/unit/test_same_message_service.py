from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from asm.application.same_indicator_supervisor import (
    SameIndicatorSupervisor,
    SameLineOutcome,
)
from asm.application.same_message_service import SameMessageService
from asm.domain.indicators import IndicatorState
from asm.domain.states import SystemState
from asm.infrastructure.fakes import (
    FakeClock,
    InMemoryDiagnosticLog,
    InMemoryDisplay,
    InMemoryIndicatorPanel,
)


@dataclass
class ManualMonotonic:
    current: float = 0.0

    def __call__(self) -> float:
        return self.current


class FailingDisplay:
    def show(self, _view: object) -> None:
        raise OSError(5, "Input/output error")


def _service():  # type: ignore[no-untyped-def]
    monotonic = ManualMonotonic()
    panel = InMemoryIndicatorPanel()
    display = InMemoryDisplay()
    log = InMemoryDiagnosticLog()
    indicators = SameIndicatorSupervisor(indicators=panel, monotonic=monotonic)
    service = SameMessageService(
        indicators=indicators,
        clock=FakeClock(datetime(2026, 9, 11, 23, 43, tzinfo=UTC)),
        display=display,
        diagnostic_log=log,
    )
    return service, monotonic, panel, display, log


def test_accepted_rwt_is_logged_presented_and_indicated() -> None:
    service, _monotonic, panel, display, log = _service()
    service.present_idle()

    outcome = service.consume("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")

    assert outcome is SameLineOutcome.ACCEPTED
    assert service.display_update_pending is True
    assert service.flush_display() is True
    assert display.history[-1].state is SystemState.RWT_ACTIVE
    assert display.history[-1].detail == "Vigencia 180 min"
    assert panel.history[-1] == IndicatorState(advisory=True, power=True)
    header_record = next(record for record in log.records if record.code == "SAME.HEADER.ACCEPTED")
    assert dict(header_record.context)["issued_code"] == "832300"
    assert dict(header_record.context)["sender"] == "XDIF/005"


def test_end_marker_is_logged_without_ending_validity() -> None:
    service, _monotonic, panel, _display, log = _service()
    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")

    assert service.consume("EAS: NNNN") is SameLineOutcome.END_OF_MESSAGE
    assert panel.history[-1].warning is True
    assert log.records[-1].code == "SAME.END"


def test_expiry_restores_idle_view_and_power_only() -> None:
    service, monotonic, panel, display, _log = _service()
    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")
    monotonic.current = 60.0

    service.poll()
    service.flush_display()

    assert display.history[-1].state is SystemState.IDLE
    assert panel.history[-1] == IndicatorState(power=True)


def test_invalid_candidate_is_preserved_as_warning_evidence() -> None:
    service, _monotonic, panel, display, log = _service()

    outcome = service.consume("EAS: ZCZC-CIV-EQW-broken")

    assert outcome is SameLineOutcome.INVALID
    assert panel.history == []
    assert display.history == []
    assert log.records[-1].code == "SAME.HEADER.INVALID"


def test_display_failure_is_logged_without_losing_accepted_header() -> None:
    monotonic = ManualMonotonic()
    panel = InMemoryIndicatorPanel()
    log = InMemoryDiagnosticLog()
    service = SameMessageService(
        indicators=SameIndicatorSupervisor(indicators=panel, monotonic=monotonic),
        clock=FakeClock(datetime(2026, 9, 11, 23, 43, tzinfo=UTC)),
        display=FailingDisplay(),
        diagnostic_log=log,
    )
    outcome = service.consume("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")

    assert outcome is SameLineOutcome.ACCEPTED
    assert panel.history[-1] == IndicatorState(advisory=True, power=True)
    assert service.flush_display() is False
    assert [record.code for record in log.records] == [
        "SAME.HEADER.ACCEPTED",
        "DISPLAY.WRITE.FAILED",
    ]
    assert service.display_update_pending is False

    service.poll()

    assert service.display_update_pending is False
