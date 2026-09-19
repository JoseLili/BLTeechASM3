"""Priority-controlled alert WAV playback with append-only evidence."""

from __future__ import annotations

from pathlib import Path

from asm.application.ports import (
    AudioPlaybackPort,
    ClockPort,
    DiagnosticLogRepository,
)
from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity
from asm.domain.priorities import EVENT_PRIORITIES
from asm.domain.states import EventType

_ASSET_NAMES: dict[EventType, str] = {
    EventType.START_RWT: "rwt.wav",
    EventType.START_EQW: "eqw.wav",
    EventType.START_SIMULACRO: "simulacro.wav",
    EventType.START_EVACUACION: "evacuacion.wav",
}


class EventAudioService:
    """Own one alert playback and enforce the operational priority order."""

    def __init__(
        self,
        *,
        player: AudioPlaybackPort,
        asset_directory: Path,
        clock: ClockPort,
        diagnostic_log: DiagnosticLogRepository,
    ) -> None:
        self._player = player
        self._asset_directory = asset_directory
        self._clock = clock
        self._diagnostic_log = diagnostic_log
        self._current_event: EventType | None = None

    @property
    def current_event(self) -> EventType | None:
        return self._current_event

    def play(self, event: EventType) -> bool:
        """Start an event WAV, preempting only lower-priority playback."""
        if event not in _ASSET_NAMES:
            raise ValueError(f"event has no alert audio asset: {event}")
        self.poll()

        current = self._current_event
        if current is not None and self._player.is_playing:
            if EVENT_PRIORITIES[event] <= EVENT_PRIORITIES[current]:
                self._append(
                    code="AUDIO.PLAYBACK.SUPPRESSED",
                    severity=DiagnosticSeverity.INFO,
                    message="Audio omitido por prioridad activa",
                    context=(("requested", event.value), ("active", current.value)),
                )
                return False
            self._player.stop()
            self._append(
                code="AUDIO.PLAYBACK.INTERRUPTED",
                severity=DiagnosticSeverity.INFO,
                message="Audio interrumpido por un evento de mayor prioridad",
                context=(("interrupted", current.value), ("replacement", event.value)),
            )
            self._current_event = None

        asset = self._asset_directory / _ASSET_NAMES[event]
        try:
            self._player.start(asset)
        except FileNotFoundError:
            self._append(
                code="AUDIO.ASSET.MISSING",
                severity=DiagnosticSeverity.WARNING,
                message="No se encontro el WAV del evento; las otras salidas continuan",
                context=(("event", event.value), ("asset", str(asset))),
            )
            return False
        except Exception as error:
            self._append(
                code="AUDIO.PLAYBACK.FAILED",
                severity=DiagnosticSeverity.WARNING,
                message="Fallo la reproduccion del WAV; las otras salidas continuan",
                context=(
                    ("event", event.value),
                    ("asset", str(asset)),
                    ("error_type", type(error).__name__),
                    ("error", str(error) or type(error).__name__),
                ),
            )
            return False

        self._current_event = event
        self._append(
            code="AUDIO.PLAYBACK.STARTED",
            severity=DiagnosticSeverity.INFO,
            message="Audio de evento iniciado por el jack analogico",
            context=(("event", event.value), ("asset", str(asset))),
        )
        return True

    def poll(self) -> None:
        """Record natural completion without blocking the application loop."""
        event = self._current_event
        if event is None or self._player.is_playing:
            return
        self._current_event = None
        self._append(
            code="AUDIO.PLAYBACK.COMPLETED",
            severity=DiagnosticSeverity.INFO,
            message="Audio de evento finalizado",
            context=(("event", event.value),),
        )

    def stop(self) -> None:
        """Stop active playback for Paro, expiry, shutdown, or replacement."""
        event = self._current_event
        if event is None:
            self._player.stop()
            return
        was_playing = self._player.is_playing
        self._player.stop()
        self._current_event = None
        self._append(
            code=("AUDIO.PLAYBACK.STOPPED" if was_playing else "AUDIO.PLAYBACK.COMPLETED"),
            severity=DiagnosticSeverity.INFO,
            message=("Audio de evento detenido" if was_playing else "Audio de evento finalizado"),
            context=(("event", event.value),),
        )

    def close(self) -> None:
        self.stop()

    def _append(
        self,
        *,
        code: str,
        severity: DiagnosticSeverity,
        message: str,
        context: tuple[tuple[str, str], ...],
    ) -> None:
        self._diagnostic_log.append(
            DiagnosticRecord(
                occurred_at=self._clock.now(),
                component="alert_audio",
                code=code,
                severity=severity,
                message=message,
                context=context,
            )
        )
