from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from asm.application.ports import MenuView, SystemView
from asm.application.same_indicator_supervisor import (
    SameIndicatorSupervisor,
    SameLineOutcome,
)
from asm.application.same_message_service import SameMessageService
from asm.domain.indicators import IndicatorState
from asm.domain.states import EventType, SystemState
from asm.infrastructure.fakes import (
    FakeClock,
    InMemoryDiagnosticLog,
    InMemoryDisplay,
    InMemoryEventAudio,
    InMemoryIndicatorPanel,
    InMemorySameNoticeRepository,
)


@dataclass
class ManualMonotonic:
    current: float = 0.0

    def __call__(self) -> float:
        return self.current


class FailingDisplay:
    def show(self, _view: object) -> None:
        raise OSError(5, "Input/output error")

    def standby(self) -> None:
        raise OSError(5, "Input/output error")


def _service(
    *,
    standby_after_rwt: bool = True,
    history: InMemorySameNoticeRepository | None = None,
    notice_observer: Any = None,
):  # type: ignore[no-untyped-def]
    monotonic = ManualMonotonic()
    panel = InMemoryIndicatorPanel()
    display = InMemoryDisplay()
    log = InMemoryDiagnosticLog()
    audio = InMemoryEventAudio()
    history = history or InMemorySameNoticeRepository()
    indicators = SameIndicatorSupervisor(indicators=panel, monotonic=monotonic)
    service = SameMessageService(
        indicators=indicators,
        clock=FakeClock(datetime(2026, 9, 11, 23, 43, tzinfo=UTC)),
        display=display,
        audio=audio,
        diagnostic_log=log,
        notice_history=history,
        monotonic=monotonic,
        rwt_notice_seconds=8.0,
        rwt_summary_seconds=5.0,
        standby_after_rwt=standby_after_rwt,
        notice_observer=notice_observer,
    )
    return service, monotonic, panel, display, audio, log


def test_accepted_rwt_is_logged_presented_and_indicated() -> None:
    service, _monotonic, panel, display, audio, log = _service()
    service.present_idle()

    outcome = service.consume("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")

    assert outcome is SameLineOutcome.ACCEPTED
    assert service.display_update_pending is True
    assert service.flush_display() is True
    assert display.history[-1].state is SystemState.RWT_ACTIVE
    assert display.history[-1].detail == "Vigencia 180 min"
    assert panel.history[-1] == IndicatorState(advisory=True, power=True)
    assert audio.played == [EventType.START_RWT]
    header_record = next(record for record in log.records if record.code == "SAME.HEADER.ACCEPTED")
    assert dict(header_record.context)["issued_code"] == "832300"
    assert dict(header_record.context)["sender"] == "XDIF/005"


def test_accepted_notice_is_persisted_and_restored_without_replaying_audio() -> None:
    history = InMemorySameNoticeRepository()
    service, _monotonic, _panel, _display, _audio, _log = _service(history=history)
    service.consume("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")
    assert len(history.records) == 1

    restored, _clock, panel, display, audio, _restored_log = _service()
    assert restored.restore_active(history.recent(limit=10)) == 1
    restored.request_status(duration_seconds=10.0)
    restored.flush_display()

    assert panel.history[-1] == IndicatorState(advisory=True, power=True)
    assert display.history[-1].footer == "RWT vigente 180m"
    assert audio.played == []


def test_accepted_notice_notifies_schedule_observer() -> None:
    observed = []
    service, _monotonic, _panel, _display, _audio, _log = _service(
        notice_observer=observed.append
    )

    service.consume("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")

    assert len(observed) == 1
    assert observed[0].header.event.value == "RWT"


def test_idle_health_footer_is_used_on_next_operator_wake() -> None:
    service, _monotonic, _panel, display, _audio, _log = _service()
    service.enter_standby()

    service.set_idle_footer("Falta RWT 20:45")
    service.request_status(duration_seconds=10.0)
    service.flush_display()

    assert display.history[-1].footer == "Falta RWT 20:45"


def test_end_marker_is_logged_without_ending_validity() -> None:
    service, _monotonic, panel, _display, audio, log = _service()
    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")

    assert service.consume("EAS: NNNN") is SameLineOutcome.END_OF_MESSAGE
    assert panel.history[-1].warning is True
    assert audio.played == [EventType.START_EQW]
    assert log.records[-1].code == "SAME.END"


def test_repeated_header_does_not_restart_audio_for_same_active_event() -> None:
    service, _monotonic, _panel, _display, audio, _log = _service()
    line = "EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-"

    service.consume(line)
    service.consume(line)

    assert audio.played == [EventType.START_RWT]


def test_rwt_banner_returns_to_waiting_view_while_validity_continues() -> None:
    service, monotonic, panel, display, audio, log = _service()
    service.consume("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")
    service.flush_display()
    monotonic.current = 8.0

    service.poll()

    assert service.display_update_pending is True
    assert service.flush_display() is True
    view = display.history[-1]
    assert view.state is SystemState.RWT_ACTIVE
    assert view.title == "Esperando evento"
    assert view.detail == "Escuchando SAME"
    assert view.footer == "RWT vigente 180m"
    assert view.compact is True
    assert panel.history[-1] == IndicatorState(advisory=True, power=True)
    assert audio.played == [EventType.START_RWT]
    assert [record.code for record in log.records].count("SAME.VISIBLE.CHANGED") == 1

    monotonic.current = 13.0
    service.poll()
    assert service.display_update_pending is True
    assert service.flush_display() is True
    assert display.standby_calls == 1


def test_eqw_stays_prominent_for_its_complete_validity() -> None:
    service, monotonic, _panel, display, _audio, _log = _service()
    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")
    service.flush_display()
    monotonic.current = 8.0

    service.poll()

    assert service.display_update_pending is False
    assert display.history[-1].state is SystemState.EQW_ACTIVE
    assert display.history[-1].compact is False


def test_continuous_display_keeps_rwt_validity_summary_visible() -> None:
    service, monotonic, _panel, display, _audio, _log = _service(
        standby_after_rwt=False
    )
    service.consume("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")
    service.flush_display()
    monotonic.current = 13.0

    service.poll()
    service.flush_display()

    assert display.history[-1].compact is True
    assert display.history[-1].footer == "RWT vigente 180m"
    assert display.standby_calls == 0


def test_enter_status_request_temporarily_wakes_standby_rwt_summary() -> None:
    service, monotonic, _panel, display, _audio, _log = _service()
    service.consume("EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-")
    service.flush_display()
    monotonic.current = 13.0
    service.poll()
    service.flush_display()
    assert display.standby_calls == 1

    service.request_status(duration_seconds=10.0)
    service.flush_display()

    assert display.history[-1].title == "Esperando evento"
    assert display.history[-1].footer == "RWT vigente 180m"

    monotonic.current = 23.0
    service.poll()
    service.flush_display()
    assert display.standby_calls == 2


def test_recent_history_view_is_temporary_and_new_eqw_preempts_it() -> None:
    service, _monotonic, _panel, display, _audio, _log = _service()
    recent = SystemView(
        state=SystemState.RWT_ACTIVE,
        title="RWT recibido",
        detail="19/09 08:45",
        footer="OK 1/2 180m",
        compact=True,
    )

    assert (
        service.request_temporary_view(
            key="history:0",
            view=recent,
            duration_seconds=10.0,
        )
        is True
    )
    service.flush_display()
    assert display.history[-1] == recent

    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")
    service.flush_display()

    assert display.history[-1].state is SystemState.EQW_ACTIVE
    assert display.history[-1].title == "ALERTA SISMICA"


def test_active_eqw_rejects_operator_history_override() -> None:
    service, _monotonic, _panel, display, _audio, _log = _service()
    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")
    service.flush_display()

    accepted = service.request_temporary_view(
        key="history:0",
        view=SystemView(
            state=SystemState.RWT_ACTIVE,
            title="RWT recibido",
            detail="19/09 08:45",
        ),
        duration_seconds=10.0,
    )

    assert accepted is False
    assert display.history[-1].state is SystemState.EQW_ACTIVE


def test_menu_page_uses_queued_display_and_eqw_preempts_it() -> None:
    service, _monotonic, _panel, display, _audio, _log = _service()
    menu = MenuView(
        title="Menu principal",
        items=("Configuracion", "Estado equipo"),
        selected_index=0,
    )

    assert service.request_menu_view(
        key="menu:root:0",
        view=menu,
        duration_seconds=10.0,
    )
    assert display.menu_history == []
    service.flush_display()
    assert display.menu_history == [menu]

    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")
    service.flush_display()
    assert display.history[-1].state is SystemState.EQW_ACTIVE


def test_confirmed_same_starts_audio_before_led_and_display() -> None:
    trace: list[str] = []

    class OrderedAudio:
        def play(self, _event: EventType) -> bool:
            trace.append("audio")
            return True

        def poll(self) -> None:
            return

        def stop(self) -> None:
            trace.append("audio-stop")

    class OrderedPanel:
        def apply(self, _state: IndicatorState) -> None:
            trace.append("led")

    class OrderedDisplay:
        def show(self, _view: object) -> None:
            trace.append("display")

        def standby(self) -> None:
            trace.append("display-standby")

    monotonic = ManualMonotonic()
    service = SameMessageService(
        indicators=SameIndicatorSupervisor(
            indicators=OrderedPanel(),
            monotonic=monotonic,
        ),
        clock=FakeClock(datetime(2026, 9, 11, 23, 43, tzinfo=UTC)),
        display=OrderedDisplay(),  # type: ignore[arg-type]
        audio=OrderedAudio(),
        diagnostic_log=InMemoryDiagnosticLog(),
        notice_history=InMemorySameNoticeRepository(),
        monotonic=monotonic,
        rwt_notice_seconds=8.0,
        rwt_summary_seconds=5.0,
        standby_after_rwt=True,
    )

    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")
    service.flush_display()

    assert trace == ["audio", "led", "display"]


def test_expiry_restores_idle_view_and_power_only() -> None:
    service, monotonic, panel, display, audio, _log = _service()
    service.consume("EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-")
    service.flush_display()
    monotonic.current = 60.0

    service.poll()
    service.flush_display()

    assert display.standby_calls == 1
    assert panel.history[-1] == IndicatorState(power=True)
    assert audio.stop_calls == 1


def test_invalid_candidate_is_preserved_as_warning_evidence() -> None:
    service, _monotonic, panel, display, audio, log = _service()

    outcome = service.consume("EAS: ZCZC-CIV-EQW-broken")

    assert outcome is SameLineOutcome.INVALID
    assert panel.history == []
    assert display.history == []
    assert audio.played == []
    assert log.records[-1].code == "SAME.HEADER.INVALID"


def test_display_failure_is_logged_without_losing_accepted_header() -> None:
    monotonic = ManualMonotonic()
    panel = InMemoryIndicatorPanel()
    log = InMemoryDiagnosticLog()
    audio = InMemoryEventAudio()
    service = SameMessageService(
        indicators=SameIndicatorSupervisor(indicators=panel, monotonic=monotonic),
        clock=FakeClock(datetime(2026, 9, 11, 23, 43, tzinfo=UTC)),
        display=FailingDisplay(),
        audio=audio,
        diagnostic_log=log,
        notice_history=InMemorySameNoticeRepository(),
        monotonic=monotonic,
        rwt_notice_seconds=8.0,
        rwt_summary_seconds=5.0,
        standby_after_rwt=True,
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
