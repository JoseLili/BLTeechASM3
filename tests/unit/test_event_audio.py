from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from asm.application.event_audio import EventAudioService
from asm.domain.states import EventType
from asm.infrastructure.fakes import FakeClock, InMemoryDiagnosticLog


@dataclass(slots=True)
class FakePlayer:
    playing: bool = False
    started: list[Path] = field(default_factory=list)
    stop_calls: int = 0

    @property
    def is_playing(self) -> bool:
        return self.playing

    def start(self, asset: Path) -> None:
        if not asset.is_file():
            raise FileNotFoundError(asset)
        self.started.append(asset)
        self.playing = True

    def stop(self) -> None:
        self.stop_calls += 1
        self.playing = False


def _service(tmp_path: Path) -> tuple[EventAudioService, FakePlayer, InMemoryDiagnosticLog]:
    for name in ("rwt.wav", "eqw.wav", "simulacro.wav", "evacuacion.wav"):
        (tmp_path / name).write_bytes(b"RIFF test")
    player = FakePlayer()
    log = InMemoryDiagnosticLog()
    service = EventAudioService(
        player=player,
        asset_directory=tmp_path,
        clock=FakeClock(datetime(2026, 9, 18, tzinfo=UTC)),
        diagnostic_log=log,
    )
    return service, player, log


def test_eqw_preempts_lower_priority_rwt(tmp_path: Path) -> None:
    service, player, log = _service(tmp_path)

    assert service.play(EventType.START_RWT) is True
    assert service.play(EventType.START_EQW) is True

    assert [path.name for path in player.started] == ["rwt.wav", "eqw.wav"]
    assert player.stop_calls == 1
    assert service.current_event is EventType.START_EQW
    assert [record.code for record in log.records] == [
        "AUDIO.PLAYBACK.STARTED",
        "AUDIO.PLAYBACK.INTERRUPTED",
        "AUDIO.PLAYBACK.STARTED",
    ]


def test_lower_priority_audio_is_suppressed(tmp_path: Path) -> None:
    service, player, log = _service(tmp_path)

    service.play(EventType.START_EVACUACION)

    assert service.play(EventType.START_SIMULACRO) is False
    assert [path.name for path in player.started] == ["evacuacion.wav"]
    assert log.records[-1].code == "AUDIO.PLAYBACK.SUPPRESSED"


def test_missing_asset_is_logged_without_raising(tmp_path: Path) -> None:
    player = FakePlayer()
    log = InMemoryDiagnosticLog()
    service = EventAudioService(
        player=player,
        asset_directory=tmp_path,
        clock=FakeClock(datetime(2026, 9, 18, tzinfo=UTC)),
        diagnostic_log=log,
    )

    assert service.play(EventType.START_RWT) is False

    assert service.current_event is None
    assert log.records[-1].code == "AUDIO.ASSET.MISSING"


def test_natural_completion_is_logged_once(tmp_path: Path) -> None:
    service, player, log = _service(tmp_path)
    service.play(EventType.START_SIMULACRO)
    player.playing = False

    service.poll()
    service.poll()

    assert service.current_event is None
    assert [record.code for record in log.records] == [
        "AUDIO.PLAYBACK.STARTED",
        "AUDIO.PLAYBACK.COMPLETED",
    ]
