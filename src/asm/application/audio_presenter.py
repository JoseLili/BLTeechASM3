"""Technology-neutral OLED presentation for WM8960 readiness."""

from __future__ import annotations

from asm.application.ports import MenuView
from asm.domain.audio import AudioDeviceStatus


def audio_status_view(status: AudioDeviceStatus) -> MenuView:
    """Present readiness facts without claiming that PCM contains useful audio."""

    def state(value: bool) -> str:
        return "OK" if value else "FALLO"

    return MenuView(
        title="Diagnostico audio",
        items=(
            f"Tarjeta: {status.card_name}",
            f"Precarga: {state(status.preload_ready)}",
            f"Captura: {state(status.capture_available)}",
            f"Salida: {state(status.playback_available)}",
        ),
        selected_index=0,
    )
