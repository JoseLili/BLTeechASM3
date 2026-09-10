from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from asm.application.channel_editor import (
    ChannelEditorOutcome,
    ChannelEditorPhase,
    ChannelRollbackError,
    ChannelStorageError,
    ReceiverChannelEditor,
)
from asm.application.menu_input import MenuCommand
from asm.application.ports import MenuView
from asm.application.receiver_service import ReceiverError, ReceiverService
from asm.domain.receiver import (
    ReceiverChannel,
    ReceiverConfigurationResult,
    ReceiverProfile,
)


@dataclass
class FakeDisplay:
    views: list[MenuView] = field(default_factory=list)

    def show_menu(self, view: MenuView) -> None:
        self.views.append(view)


@dataclass
class FakeReceiver:
    requests: list[ReceiverProfile] = field(default_factory=list)
    fail_next: bool = False

    def configure(self, profile: ReceiverProfile) -> ReceiverConfigurationResult:
        self.requests.append(profile)
        if self.fail_next:
            self.fail_next = False
            raise ReceiverError("receiver unavailable")
        return ReceiverConfigurationResult("fake", profile, ("ok",), True)


@dataclass
class FakeRepository:
    current: ReceiverChannel | None = None
    saves: list[ReceiverChannel] = field(default_factory=list)
    fail_save: bool = False

    def load(self) -> ReceiverChannel | None:
        return self.current

    def save(self, channel: ReceiverChannel) -> None:
        if self.fail_save:
            raise ChannelStorageError("disk unavailable")
        self.current = channel
        self.saves.append(channel)


def _editor() -> tuple[ReceiverChannelEditor, FakeDisplay, FakeReceiver, FakeRepository]:
    display = FakeDisplay()
    receiver = FakeReceiver()
    repository = FakeRepository(current=ReceiverChannel.C7)
    editor = ReceiverChannelEditor(
        display=display,
        receiver=ReceiverService(receiver),
        repository=repository,
        committed_channel=ReceiverChannel.C7,
    )
    return editor, display, receiver, repository


def test_selection_contains_only_seven_derived_channels_and_wraps() -> None:
    editor, display, _receiver, _repository = _editor()

    view = editor.open()
    editor.handle(MenuCommand.MOVE_DOWN)

    assert view.items == (
        "C1 162.4000",
        "C2 162.4250",
        "C3 162.4500",
        "C4 162.4750",
        "C5 162.5000",
        "C6 162.5250",
        "C7 162.5500",
    )
    assert editor.candidate_channel is ReceiverChannel.C1
    assert display.views[-1].selected_index == 0


def test_first_enter_verifies_and_second_enter_persists() -> None:
    editor, display, receiver, repository = _editor()
    editor.open()
    editor.handle(MenuCommand.MOVE_UP)

    assert editor.handle(MenuCommand.CONFIRM) is ChannelEditorOutcome.NONE
    assert editor.phase is ChannelEditorPhase.VERIFIED
    assert receiver.requests[-1].channel is ReceiverChannel.C6
    assert repository.saves == []
    assert display.views[-1].title == "C6 verificado"

    assert editor.handle(MenuCommand.CONFIRM) is ChannelEditorOutcome.SAVED
    assert editor.is_open is False
    assert editor.committed_channel is ReceiverChannel.C6
    assert repository.saves == [ReceiverChannel.C6]


def test_back_after_verification_restores_committed_channel() -> None:
    editor, _display, receiver, repository = _editor()
    editor.open()
    editor.handle(MenuCommand.MOVE_UP)
    editor.handle(MenuCommand.CONFIRM)

    assert editor.handle(MenuCommand.GO_BACK) is ChannelEditorOutcome.CLOSED
    assert [request.channel for request in receiver.requests] == [
        ReceiverChannel.C6,
        ReceiverChannel.C7,
    ]
    assert repository.saves == []
    assert editor.committed_channel is ReceiverChannel.C7


def test_failed_apply_stays_open_and_never_saves() -> None:
    editor, display, receiver, repository = _editor()
    editor.open()
    receiver.fail_next = True

    assert editor.handle(MenuCommand.CONFIRM) is ChannelEditorOutcome.APPLY_FAILED
    assert editor.is_open is True
    assert editor.phase is ChannelEditorPhase.SELECTING
    assert repository.saves == []
    assert display.views[-1].title == "Fallo SA818"


def test_failed_save_rolls_hardware_back_to_committed_channel() -> None:
    editor, display, receiver, repository = _editor()
    repository.fail_save = True
    editor.open()
    editor.handle(MenuCommand.MOVE_UP)
    editor.handle(MenuCommand.CONFIRM)

    assert editor.handle(MenuCommand.CONFIRM) is ChannelEditorOutcome.SAVE_FAILED
    assert [request.channel for request in receiver.requests] == [
        ReceiverChannel.C6,
        ReceiverChannel.C7,
    ]
    assert editor.is_open is True
    assert editor.candidate_channel is ReceiverChannel.C7
    assert display.views[-1].title == "No se guardo"


def test_failed_rollback_is_escalated_as_a_distinct_error() -> None:
    editor, _display, receiver, _repository = _editor()
    editor.open()
    editor.handle(MenuCommand.MOVE_UP)
    editor.handle(MenuCommand.CONFIRM)
    receiver.fail_next = True

    with pytest.raises(ChannelRollbackError, match="could not restore C7"):
        editor.handle(MenuCommand.GO_BACK)

