"""Debounced Mean Well change detection, evidence, and OLED notification."""

from __future__ import annotations

from collections.abc import Callable

from asm.application.ports import (
    ClockPort,
    DiagnosticDisplayPort,
    DiagnosticLogRepository,
    DiagnosticView,
    PowerMonitorPort,
)
from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity
from asm.domain.power import PowerSignal, SignalState

_SIGNAL_LABELS: dict[PowerSignal, str] = {
    PowerSignal.AC_OK: "Red CA disponible",
    PowerSignal.BATTERY_DISCONNECTED: "Bateria desconectada",
    PowerSignal.BATTERY_LOW: "Bateria baja",
    PowerSignal.BATTERY_FULL: "Bateria llena",
    PowerSignal.DISCHARGING: "Operacion en bateria",
}

_STATE_LABELS: dict[SignalState, str] = {
    SignalState.ASSERTED: "SI",
    SignalState.CLEAR: "NO",
    SignalState.UNKNOWN: "DESCONOCIDO",
}


class PowerSupervisor:
    """Publish only input changes that remain stable for the configured window."""

    def __init__(
        self,
        *,
        monitor: PowerMonitorPort,
        clock: ClockPort,
        monotonic: Callable[[], float],
        display: DiagnosticDisplayPort,
        diagnostic_log: DiagnosticLogRepository,
        debounce_seconds: float,
    ) -> None:
        if debounce_seconds <= 0:
            raise ValueError("debounce_seconds must be greater than zero")
        self._monitor = monitor
        self._clock = clock
        self._monotonic = monotonic
        self._display = display
        self._diagnostic_log = diagnostic_log
        self._debounce_seconds = debounce_seconds
        self._published: dict[PowerSignal, SignalState] | None = None
        self._pending: dict[PowerSignal, tuple[SignalState, float]] = {}

    def poll(self) -> tuple[DiagnosticRecord, ...]:
        """Sample once and publish any independently debounced transitions."""
        sample = self._monitor.read()
        now = self._monotonic()
        if self._published is None:
            self._published = {signal: sample.state_for(signal) for signal in PowerSignal}
            return ()

        records: list[DiagnosticRecord] = []
        for signal in PowerSignal:
            current = sample.state_for(signal)
            previous = self._published[signal]
            if current is previous:
                self._pending.pop(signal, None)
                continue

            pending = self._pending.get(signal)
            if pending is None or pending[0] is not current:
                self._pending[signal] = (current, now)
                continue
            if now - pending[1] < self._debounce_seconds:
                continue

            record = self._record(signal, previous, current)
            self._diagnostic_log.append(record)
            records.append(record)
            self._published[signal] = current
            self._pending.pop(signal, None)

        if records:
            severity = (
                DiagnosticSeverity.WARNING
                if any(record.severity is DiagnosticSeverity.WARNING for record in records)
                else DiagnosticSeverity.INFO
            )
            lines = tuple(record.message for record in records[:3])
            if len(records) > 3:
                lines = (*lines[:2], f"+{len(records) - 2} cambios")
            self._display.show_diagnostic(
                DiagnosticView(title="Aviso de energia", lines=lines, severity=severity)
            )
        return tuple(records)

    def _record(
        self,
        signal: PowerSignal,
        previous: SignalState,
        current: SignalState,
    ) -> DiagnosticRecord:
        message = f"{_SIGNAL_LABELS[signal]}: {_STATE_LABELS[current]}"
        return DiagnosticRecord(
            occurred_at=self._clock.now(),
            component="meanwell",
            code=f"POWER.{signal.value}.{current.value}",
            severity=(
                DiagnosticSeverity.WARNING
                if current is SignalState.UNKNOWN
                else DiagnosticSeverity.INFO
            ),
            message=message,
            context=(
                ("signal", signal.value),
                ("previous", previous.value),
                ("current", current.value),
            ),
        )
