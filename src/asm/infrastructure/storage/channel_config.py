"""Atomic JSON persistence for the last confirmed receiver channel."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import suppress
from pathlib import Path

from asm.application.channel_editor import ChannelStorageError
from asm.domain.receiver import ReceiverChannel


class JsonReceiverChannelRepository:
    """Store a versioned channel document without storing a separate frequency."""

    SCHEMA_VERSION = 1

    def __init__(self, path: Path) -> None:
        self._path = path.expanduser()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> ReceiverChannel | None:
        """Return None only when no configuration has been created yet."""
        if not self._path.exists():
            return None
        try:
            document = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(document, dict):
                raise ValueError("root must be an object")
            if document.get("schema_version") != self.SCHEMA_VERSION:
                raise ValueError("unsupported schema_version")
            channel = document.get("channel")
            if not isinstance(channel, str):
                raise ValueError("channel must be text")
            return ReceiverChannel(channel)
        except (OSError, ValueError) as error:
            raise ChannelStorageError(f"invalid channel configuration: {self._path}") from error

    def save(self, channel: ReceiverChannel) -> None:
        """Replace the document atomically after flushing its temporary file."""
        temporary_path: Path | None = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(
                    {"schema_version": self.SCHEMA_VERSION, "channel": channel.value},
                    temporary,
                    indent=2,
                )
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self._path)
        except OSError as error:
            if temporary_path is not None:
                with suppress(OSError):
                    temporary_path.unlink(missing_ok=True)
            raise ChannelStorageError(f"could not save channel: {self._path}") from error
