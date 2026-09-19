from __future__ import annotations

import json
from pathlib import Path

import pytest

from asm.application.channel_editor import ChannelStorageError
from asm.domain.receiver import ReceiverChannel
from asm.infrastructure.storage.channel_config import JsonReceiverChannelRepository


def test_missing_document_uses_callers_factory_default(tmp_path: Path) -> None:
    repository = JsonReceiverChannelRepository(tmp_path / "receiver.json")

    assert repository.load() is None


def test_save_and_load_round_trip_contains_no_independent_frequency(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "receiver.json"
    repository = JsonReceiverChannelRepository(path)

    repository.save(ReceiverChannel.C4)

    assert repository.load() is ReceiverChannel.C4
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "schema_version": 1,
        "channel": "C4",
    }
    assert not list(path.parent.glob("*.tmp"))


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "[]",
        '{"schema_version": 2, "channel": "C7"}',
        '{"schema_version": 1, "channel": "C8"}',
    ],
)
def test_invalid_document_is_rejected(tmp_path: Path, content: str) -> None:
    path = tmp_path / "receiver.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ChannelStorageError, match="invalid channel configuration"):
        JsonReceiverChannelRepository(path).load()

