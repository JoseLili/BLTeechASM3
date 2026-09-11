from __future__ import annotations

from dataclasses import dataclass

from asm.application.same_indicator_supervisor import (
    SameIndicatorSupervisor,
    SameLineOutcome,
)
from asm.domain.indicators import IndicatorState
from asm.infrastructure.fakes import InMemoryIndicatorPanel


@dataclass
class ManualMonotonic:
    current: float = 0.0

    def __call__(self) -> float:
        return self.current


def _supervisor():  # type: ignore[no-untyped-def]
    panel = InMemoryIndicatorPanel()
    clock = ManualMonotonic()
    supervisor = SameIndicatorSupervisor(indicators=panel, monotonic=clock)
    return supervisor, panel, clock


def test_rwt_blinks_slowly_and_expires_after_three_hours() -> None:
    supervisor, panel, clock = _supervisor()

    assert (
        supervisor.handle_line("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")
        is SameLineOutcome.ACCEPTED
    )
    assert panel.history[-1] == IndicatorState(advisory=True, power=True)

    clock.current = 1.0
    supervisor.poll()
    assert panel.history[-1] == IndicatorState(power=True)
    clock.current = 2.0
    supervisor.poll()
    assert panel.history[-1] == IndicatorState(advisory=True, power=True)
    clock.current = 10_800.0
    supervisor.poll()
    assert panel.history[-1] == IndicatorState(power=True)

def test_nnnn_does_not_cancel_the_active_notice() -> None:
    supervisor, panel, _clock = _supervisor()
    supervisor.handle_line("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")

    assert supervisor.handle_line("EAS: NNNN") is SameLineOutcome.END_OF_MESSAGE
    assert panel.history[-1].warning is True


def test_invalid_header_fails_closed_without_touching_outputs() -> None:
    supervisor, panel, _clock = _supervisor()

    assert (
        supervisor.handle_line("EAS: ZCZC-CIV-EQW-000000+0060-invalid-")
        is SameLineOutcome.INVALID
    )
    assert panel.history == []


def test_duplicate_header_does_not_restart_the_notice() -> None:
    supervisor, panel, clock = _supervisor()
    line = "EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-"
    supervisor.handle_line(line)
    clock.current = 3.0

    assert supervisor.handle_line(line) is SameLineOutcome.DUPLICATE
    clock.current = 60.0
    supervisor.poll()
    assert panel.history[-1] == IndicatorState(power=True)
