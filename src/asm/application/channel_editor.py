"""Transactional C1-C7 editor for the local OLED menu."""

from __future__ import annotations

from enum import StrEnum

from asm.application.menu_input import MenuCommand
from asm.application.ports import MenuDisplayPort, MenuView, ReceiverChannelRepository
from asm.application.receiver_service import ReceiverError, ReceiverService
from asm.domain.receiver import ReceiverChannel, ReceiverProfile


class ChannelStorageError(RuntimeError):
    """Persistent channel state is missing, corrupt, or cannot be saved."""


class ChannelRollbackError(ReceiverError):
    """The previously committed channel could not be restored."""


class ChannelEditorPhase(StrEnum):
    """Two explicit stages prevent an unverified selection from being saved."""

    SELECTING = "SELECTING"
    VERIFIED = "VERIFIED"


class ChannelEditorOutcome(StrEnum):
    """Observable result of handling one menu command."""

    NONE = "NONE"
    CLOSED = "CLOSED"
    SAVED = "SAVED"
    APPLY_FAILED = "APPLY_FAILED"
    SAVE_FAILED = "SAVE_FAILED"


class ReceiverChannelEditor:
    """Select, verify, confirm, persist, or roll back one fixed channel."""

    def __init__(
        self,
        *,
        display: MenuDisplayPort,
        receiver: ReceiverService,
        repository: ReceiverChannelRepository,
        committed_channel: ReceiverChannel,
    ) -> None:
        self._display = display
        self._receiver = receiver
        self._repository = repository
        self._committed = committed_channel
        self._candidate = committed_channel
        self._phase = ChannelEditorPhase.SELECTING
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def committed_channel(self) -> ReceiverChannel:
        return self._committed

    @property
    def candidate_channel(self) -> ReceiverChannel:
        return self._candidate

    @property
    def phase(self) -> ChannelEditorPhase:
        return self._phase

    def open(self) -> MenuView:
        """Start a fresh edit at the last confirmed channel."""
        self._candidate = self._committed
        self._phase = ChannelEditorPhase.SELECTING
        self._open = True
        return self._render_selection()

    def handle(self, command: MenuCommand) -> ChannelEditorOutcome:
        """Apply one command without ever accepting an arbitrary frequency."""
        if not self._open:
            return ChannelEditorOutcome.NONE
        if self._phase is ChannelEditorPhase.VERIFIED:
            return self._handle_verified(command)

        if command in (MenuCommand.MOVE_UP, MenuCommand.MOVE_DOWN):
            direction = -1 if command is MenuCommand.MOVE_UP else 1
            channels = tuple(ReceiverChannel)
            index = (channels.index(self._candidate) + direction) % len(channels)
            self._candidate = channels[index]
            self._render_selection()
        elif command in (MenuCommand.MOVE_LEFT, MenuCommand.GO_BACK):
            self._open = False
            return ChannelEditorOutcome.CLOSED
        elif command in (MenuCommand.MOVE_RIGHT, MenuCommand.CONFIRM):
            return self._apply_candidate()
        return ChannelEditorOutcome.NONE

    def _apply_candidate(self) -> ChannelEditorOutcome:
        self._display.show_menu(
            MenuView(
                title=f"Aplicando {self._candidate.value}",
                items=(f"{self._candidate.frequency_text} MHz", "Verificando SA818"),
                selected_index=0,
            )
        )
        try:
            self._receiver.configure(ReceiverProfile.gold(self._candidate))
        except ReceiverError as error:
            self._render_error("Fallo SA818", str(error))
            return ChannelEditorOutcome.APPLY_FAILED

        self._phase = ChannelEditorPhase.VERIFIED
        self._display.show_menu(
            MenuView(
                title=f"{self._candidate.value} verificado",
                items=("Enter: guardar", "Regresar: cancelar"),
                selected_index=0,
            )
        )
        return ChannelEditorOutcome.NONE

    def _handle_verified(self, command: MenuCommand) -> ChannelEditorOutcome:
        if command in (MenuCommand.MOVE_RIGHT, MenuCommand.CONFIRM):
            return self._save_candidate()
        if command in (MenuCommand.MOVE_LEFT, MenuCommand.GO_BACK):
            self._restore_committed()
            self._open = False
            self._phase = ChannelEditorPhase.SELECTING
            return ChannelEditorOutcome.CLOSED
        return ChannelEditorOutcome.NONE

    def _save_candidate(self) -> ChannelEditorOutcome:
        try:
            self._repository.save(self._candidate)
        except ChannelStorageError as error:
            self._restore_committed()
            self._candidate = self._committed
            self._phase = ChannelEditorPhase.SELECTING
            self._render_error("No se guardo", str(error))
            return ChannelEditorOutcome.SAVE_FAILED

        self._committed = self._candidate
        self._open = False
        self._phase = ChannelEditorPhase.SELECTING
        return ChannelEditorOutcome.SAVED

    def _restore_committed(self) -> None:
        self._display.show_menu(
            MenuView(
                title=f"Restaurando {self._committed.value}",
                items=(f"{self._committed.frequency_text} MHz", "Espere..."),
                selected_index=0,
            )
        )
        try:
            self._receiver.configure(ReceiverProfile.gold(self._committed))
        except ReceiverError as error:
            raise ChannelRollbackError(
                f"could not restore {self._committed.value}: {error}"
            ) from error

    def _render_selection(self) -> MenuView:
        channels = tuple(ReceiverChannel)
        view = MenuView(
            title=f"Canal actual {self._committed.value}",
            items=tuple(
                f"{channel.value} {channel.frequency_text}" for channel in channels
            ),
            selected_index=channels.index(self._candidate),
        )
        self._display.show_menu(view)
        return view

    def _render_error(self, title: str, detail: str) -> None:
        self._display.show_menu(
            MenuView(
                title=title,
                items=(detail, f"Sigue {self._committed.value}", "Enter: reintentar"),
                selected_index=0,
            )
        )
