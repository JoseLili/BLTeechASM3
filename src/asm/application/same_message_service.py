"""Audit, present, and indicate decoded SAME messages."""

from __future__ import annotations

from asm.application.ports import (
    ClockPort,
    DiagnosticLogRepository,
    DisplayPort,
    SystemView,
)
from asm.application.same_indicator_supervisor import (
    SameIndicatorSupervisor,
    SameLineOutcome,
)
from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity
from asm.domain.same import (
    SameEndOfMessage,
    SameEventCode,
    SameHeader,
    SameIndicatorSnapshot,
    SameParseError,
    parse_multimon_same_line,
)
from asm.domain.states import SystemState


class SameMessageService:
    """Consume decoder text while keeping raw evidence for every decision."""

    def __init__(
        self,
        *,
        indicators: SameIndicatorSupervisor,
        clock: ClockPort,
        display: DisplayPort,
        diagnostic_log: DiagnosticLogRepository,
    ) -> None:
        self._indicators = indicators
        self._clock = clock
        self._display = display
        self._diagnostic_log = diagnostic_log
        self._visible_event: SameEventCode | None = None

    def present_idle(self) -> None:
        self._visible_event = None
        self._display.show(
            SystemView(state=SystemState.IDLE, title="Sistema listo", detail="Escuchando SAME")
        )

    def consume(self, line: str) -> SameLineOutcome:
        try:
            decoded = parse_multimon_same_line(line)
        except SameParseError as error:
            if "ZCZC-" in line:
                self._append(
                    code="SAME.HEADER.INVALID",
                    severity=DiagnosticSeverity.WARNING,
                    message=str(error),
                    context=(("raw", line.strip()),),
                )
            return SameLineOutcome.INVALID
        if decoded is None:
            return SameLineOutcome.IGNORED
        if isinstance(decoded, SameEndOfMessage):
            self._append(
                code="SAME.END",
                severity=DiagnosticSeverity.INFO,
                message="Fin de trama SAME recibido; la vigencia continúa",
            )
            return SameLineOutcome.END_OF_MESSAGE

        outcome = self._indicators.handle_header(decoded)
        self._log_header(decoded, outcome)
        self._present_if_changed()
        return outcome

    def poll(self) -> None:
        self._present_if_changed(self._indicators.poll())

    def _present_if_changed(self, snapshot: SameIndicatorSnapshot | None = None) -> None:
        if snapshot is None:
            snapshot = self._indicators.poll()
        if snapshot.event is self._visible_event:
            return
        previous = self._visible_event
        self._visible_event = snapshot.event
        if snapshot.event is None:
            self.present_idle()
        else:
            state = (
                SystemState.RWT_ACTIVE
                if snapshot.event is SameEventCode.RWT
                else SystemState.EQW_ACTIVE
            )
            title = "AVISO RWT" if snapshot.event is SameEventCode.RWT else "ALERTA SISMICA"
            remaining_minutes = max(1, int((snapshot.expires_in_seconds + 59) // 60))
            self._display.show(
                SystemView(
                    state=state,
                    title=title,
                    detail=f"Vigencia {remaining_minutes} min",
                )
            )
        self._append(
            code="SAME.VISIBLE.CHANGED",
            severity=DiagnosticSeverity.INFO,
            message="Cambio de aviso SAME visible",
            context=(
                ("previous", previous.value if previous is not None else "NONE"),
                ("current", snapshot.event.value if snapshot.event is not None else "NONE"),
            ),
        )

    def _log_header(self, header: SameHeader, outcome: SameLineOutcome) -> None:
        self._append(
            code=f"SAME.HEADER.{outcome.value}",
            severity=DiagnosticSeverity.INFO,
            message=f"Cabecera {header.event.value} {outcome.value.lower()}",
            context=(
                ("raw", header.raw),
                ("event", header.event.value),
                ("areas", ",".join(header.area_codes)),
                ("all_units", str(header.applies_to_all_units).lower()),
                ("validity_seconds", str(int(header.validity.total_seconds()))),
                ("issued_code", header.issued_code),
                ("sender", header.sender),
            ),
        )

    def _append(
        self,
        *,
        code: str,
        severity: DiagnosticSeverity,
        message: str,
        context: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self._diagnostic_log.append(
            DiagnosticRecord(
                occurred_at=self._clock.now(),
                component="same_decoder",
                code=code,
                severity=severity,
                message=message,
                context=context,
            )
        )
