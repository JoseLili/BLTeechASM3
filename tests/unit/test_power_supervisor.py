from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from asm.application.power_supervisor import PowerSupervisor
from asm.domain.diagnostics import DiagnosticSeverity
from asm.domain.power import PowerStatus, SignalState
from asm.infrastructure.fakes import (
    FakeClock,
    InMemoryDiagnosticLog,
    InMemoryDisplay,
)


def _status(
    *,
    ac_ok: SignalState = SignalState.CLEAR,
    battery_disconnected: SignalState = SignalState.CLEAR,
    battery_low: SignalState = SignalState.CLEAR,
    battery_full: SignalState = SignalState.CLEAR,
    discharging: SignalState = SignalState.CLEAR,
) -> PowerStatus:
    return PowerStatus(
        ac_ok=ac_ok,
        battery_disconnected=battery_disconnected,
        battery_low=battery_low,
        battery_full=battery_full,
        discharging=discharging,
    )


@dataclass
class MutableMonitor:
    status: PowerStatus

    def read(self) -> PowerStatus:
        return self.status


@dataclass
class ManualMonotonic:
    current: float = 0.0

    def __call__(self) -> float:
        return self.current


def _supervisor() -> tuple[
    PowerSupervisor,
    MutableMonitor,
    ManualMonotonic,
    InMemoryDisplay,
    InMemoryDiagnosticLog,
]:
    monitor = MutableMonitor(_status())
    monotonic = ManualMonotonic()
    display = InMemoryDisplay()
    diagnostic_log = InMemoryDiagnosticLog()
    supervisor = PowerSupervisor(
        monitor=monitor,
        clock=FakeClock(datetime(2026, 9, 10, tzinfo=UTC)),
        monotonic=monotonic,
        display=display,
        diagnostic_log=diagnostic_log,
        debounce_seconds=0.25,
    )
    return supervisor, monitor, monotonic, display, diagnostic_log


def test_baseline_is_silent_and_stable_change_is_logged_and_shown() -> None:
    supervisor, monitor, monotonic, display, diagnostic_log = _supervisor()
    assert supervisor.poll() == ()

    monitor.status = _status(battery_low=SignalState.ASSERTED)
    assert supervisor.poll() == ()
    monotonic.current = 0.249
    assert supervisor.poll() == ()
    monotonic.current = 0.25
    records = supervisor.poll()

    assert len(records) == 1
    assert records[0].code == "POWER.BATTERY_LOW.ASSERTED"
    assert records[0].context == (
        ("signal", "BATTERY_LOW"),
        ("previous", "CLEAR"),
        ("current", "ASSERTED"),
    )
    assert diagnostic_log.records == list(records)
    assert display.diagnostics[0].lines == ("Bateria baja: SI",)


def test_short_glitch_is_not_published() -> None:
    supervisor, monitor, monotonic, display, diagnostic_log = _supervisor()
    supervisor.poll()
    monitor.status = _status(ac_ok=SignalState.ASSERTED)
    supervisor.poll()

    monotonic.current = 0.1
    monitor.status = _status()
    supervisor.poll()
    monotonic.current = 1.0
    supervisor.poll()

    assert diagnostic_log.records == []
    assert display.diagnostics == []


def test_signals_debounce_independently() -> None:
    supervisor, monitor, monotonic, _display, diagnostic_log = _supervisor()
    supervisor.poll()
    monitor.status = _status(battery_low=SignalState.ASSERTED)
    supervisor.poll()

    monotonic.current = 0.1
    monitor.status = _status(
        battery_low=SignalState.ASSERTED,
        battery_disconnected=SignalState.ASSERTED,
    )
    supervisor.poll()
    monotonic.current = 0.25
    supervisor.poll()

    assert [record.code for record in diagnostic_log.records] == [
        "POWER.BATTERY_LOW.ASSERTED"
    ]

    monotonic.current = 0.36
    supervisor.poll()
    assert [record.code for record in diagnostic_log.records] == [
        "POWER.BATTERY_LOW.ASSERTED",
        "POWER.BATTERY_DISCONNECTED.ASSERTED",
    ]


def test_unknown_input_is_visible_as_warning_not_invented_as_normal() -> None:
    supervisor, monitor, monotonic, display, diagnostic_log = _supervisor()
    supervisor.poll()
    monitor.status = _status(ac_ok=SignalState.UNKNOWN)
    supervisor.poll()
    monotonic.current = 0.25
    records = supervisor.poll()

    assert records[0].severity is DiagnosticSeverity.WARNING
    assert diagnostic_log.records[0].message == "Red CA disponible: DESCONOCIDO"
    assert display.diagnostics[0].severity is DiagnosticSeverity.WARNING
