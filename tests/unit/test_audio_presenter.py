from __future__ import annotations

from asm.application.audio_presenter import audio_status_view
from asm.domain.audio import AudioDeviceStatus


def test_audio_status_view_keeps_enumeration_separate_from_preload() -> None:
    view = audio_status_view(
        AudioDeviceStatus(
            card_name="wm8960soundcard",
            preload_ready=False,
            capture_available=True,
            playback_available=True,
        )
    )

    assert view.title == "Diagnostico audio"
    assert view.items == (
        "Tarjeta: wm8960soundcard",
        "Precarga: FALLO",
        "Captura: OK",
        "Salida: OK",
    )
