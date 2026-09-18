"""Audit, present, and indicate decoded SAME messages."""

from __future__ import annotations

from asm.application.ports import (
    ClockPort,
    DiagnosticLogRepository,
    DisplayPort,
    EventAudioPort,
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
from asm.domain.states import EventType, SystemState

_UNSET = object()


class SameMessageService:
    """Consume decoder text while keeping raw evidence for every decision."""

    def __init__(
        self,
        *,
        indicators: SameIndicatorSupervisor,
        clock: ClockPort,
        display: DisplayPort,
        audio: EventAudioPort,
        diagnostic_log: DiagnosticLogRepository,
    ) -> None:
        self._indicators = indicators
        self._clock = clock
        self._display = display
        self._audio = audio
        self._diagnostic_log = diagnostic_log
        self._visible_event: SameEventCode | None = None
        self._attempted_event: SameEventCode | None | object = _UNSET
        self._pending_display: tuple[SameEventCode | None, SystemView, bool] | None = None

    @property
    def display_update_pending(self) -> bool:
        """Return whether the daemon must open a safe display-write window."""
        return self._pending_display is not None

    def present_idle(self) -> None:
        """Present the initial idle view before the decoder stream starts."""
        self._queue_display(
            event=None,
            view=SystemView(
                state=SystemState.IDLE,
                title="Sistema listo",
                detail="Escuchando SAME",
            ),
            log_change=False,
        )
        self.flush_display()

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

        outcome = self._indicators.track_header(decoded)
        snapshot = self._indicators.snapshot()
        self._start_audio_if_changed(snapshot)
        self._log_header(decoded, outcome)
        self._indicators.apply_snapshot(snapshot)
        self._present_if_changed(snapshot)
        return outcome

    def poll(self) -> None:
        self._audio.poll()
        snapshot = self._indicators.snapshot()
        self._start_audio_if_changed(snapshot)
        self._indicators.apply_snapshot(snapshot)
        self._present_if_changed(snapshot)

    def flush_display(self) -> bool:
        """Attempt one queued write without allowing display I/O to escape.

        Carrier Rev A can reject I2C writes while I2S clocks are active. The
        daemon therefore calls this only after pausing the decoder stream.
        Failed writes are audited once and never cause a tight retry loop.
        """
        pending = self._pending_display
        if pending is None:
            return True
        self._pending_display = None
        event, view, log_change = pending
        previous = self._visible_event
        try:
            self._display.show(view)
        except Exception as error:
            self._append(
                code="DISPLAY.WRITE.FAILED",
                severity=DiagnosticSeverity.WARNING,
                message="No fue posible actualizar la pantalla; la recepcion continua",
                context=(
                    ("requested", event.value if event is not None else "IDLE"),
                    ("error_type", type(error).__name__),
                    ("error", str(error) or type(error).__name__),
                ),
            )
            return False

        self._visible_event = event
        if log_change:
            self._append(
                code="SAME.VISIBLE.CHANGED",
                severity=DiagnosticSeverity.INFO,
                message="Cambio de aviso SAME visible",
                context=(
                    ("previous", previous.value if previous is not None else "NONE"),
                    ("current", event.value if event is not None else "NONE"),
                ),
            )
        return True

    def _present_if_changed(self, snapshot: SameIndicatorSnapshot | None = None) -> None:
        if snapshot is None:
            snapshot = self._indicators.poll()
        if snapshot.event is self._attempted_event:
            return
        if snapshot.event is None:
            view = SystemView(
                state=SystemState.IDLE,
                title="Sistema listo",
                detail="Escuchando SAME",
            )
        else:
            state = (
                SystemState.RWT_ACTIVE
                if snapshot.event is SameEventCode.RWT
                else SystemState.EQW_ACTIVE
            )
            title = "AVISO RWT" if snapshot.event is SameEventCode.RWT else "ALERTA SISMICA"
            remaining_minutes = max(1, int((snapshot.expires_in_seconds + 59) // 60))
            view = SystemView(
                state=state,
                title=title,
                detail=f"Vigencia {remaining_minutes} min",
            )
        self._queue_display(event=snapshot.event, view=view, log_change=True)

    def _start_audio_if_changed(self, snapshot: SameIndicatorSnapshot) -> None:
        """Start audio before LED/display whenever the visible event changes."""
        if snapshot.event is self._attempted_event:
            return
        if snapshot.event is None:
            self._audio.stop()
            return
        event = (
            EventType.START_RWT
            if snapshot.event is SameEventCode.RWT
            else EventType.START_EQW
        )
        self._audio.play(event)

    def _queue_display(
        self,
        *,
        event: SameEventCode | None,
        view: SystemView,
        log_change: bool,
    ) -> None:
        self._attempted_event = event
        self._pending_display = (event, view, log_change)

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
