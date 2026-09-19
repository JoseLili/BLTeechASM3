from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from asm.domain.receiver import ReceiverChannel, ReceiverProfile
from asm.infrastructure.receiver.sa818_serial import (
    Sa818ProtocolError,
    Sa818RejectedError,
    Sa818SerialReceiver,
    Sa818TimeoutError,
    Sa818VerificationError,
)


@dataclass
class FakeSerial:
    responses: list[bytes]
    writes: list[bytes] = field(default_factory=list)
    resets: int = 0
    flushes: int = 0
    closes: int = 0
    short_write: bool = False

    def reset_input_buffer(self) -> None:
        self.resets += 1

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data) - 1 if self.short_write else len(data)

    def flush(self) -> None:
        self.flushes += 1

    def readline(self) -> bytes:
        return self.responses.pop(0)

    def close(self) -> None:
        self.closes += 1


def _success_responses(frequency: str = "162.5500") -> list[bytes]:
    return [
        b"+DMOCONNECT:0\r\n",
        b"+DMOSETGROUP:0\r\n",
        b"+DMOSETVOLUME:0\r\n",
        b"+DMOSETFILTER:0\r\n",
        f"+DMOREADGROUP:1,{frequency},{frequency},0000,0,0000\r\n".encode(),
    ]


def test_configure_emits_gold_sequence_and_verifies_readback() -> None:
    serial = FakeSerial(_success_responses())
    sleeps: list[float] = []
    receiver = Sa818SerialReceiver(serial_port=serial, sleep=sleeps.append)

    result = receiver.configure(ReceiverProfile.gold())

    assert serial.writes == [
        b"AT+DMOCONNECT\r\n",
        b"AT+DMOSETGROUP=1,162.5500,162.5500,0000,0,0000\r\n",
        b"AT+DMOSETVOLUME=6\r\n",
        b"AT+SETFILTER=0,0,0\r\n",
        b"AT+DMOREADGROUP\r\n",
    ]
    assert serial.resets == 1
    assert serial.flushes == 5
    assert sleeps == [1.0]
    assert result.verified is True
    assert result.profile.channel is ReceiverChannel.C7
    assert result.responses[-1].startswith("+DMOREADGROUP:1,162.5500")


def test_settle_delay_occurs_only_once_for_reconfiguration() -> None:
    serial = FakeSerial(_success_responses() + _success_responses("162.5250"))
    sleeps: list[float] = []
    receiver = Sa818SerialReceiver(serial_port=serial, sleep=sleeps.append)

    receiver.configure(ReceiverProfile.gold())
    receiver.configure(ReceiverProfile.gold(ReceiverChannel.C6))

    assert sleeps == [1.0]
    assert serial.resets == 2


def test_timeout_stops_without_sending_later_commands() -> None:
    serial = FakeSerial([b""])
    receiver = Sa818SerialReceiver(serial_port=serial, settle_seconds=0)

    with pytest.raises(Sa818TimeoutError, match="DMOCONNECT"):
        receiver.configure(ReceiverProfile.gold())

    assert serial.writes == [b"AT+DMOCONNECT\r\n"]


def test_explicit_rejection_is_distinct_from_malformed_response() -> None:
    serial = FakeSerial([b"+DMOCONNECT:1\r\n"])
    receiver = Sa818SerialReceiver(serial_port=serial, settle_seconds=0)

    with pytest.raises(Sa818RejectedError, match="rejected"):
        receiver.configure(ReceiverProfile.gold())


def test_readback_mismatch_never_reports_verified() -> None:
    serial = FakeSerial(_success_responses("162.5250"))
    receiver = Sa818SerialReceiver(serial_port=serial, settle_seconds=0)

    with pytest.raises(Sa818VerificationError, match="readback mismatch"):
        receiver.configure(ReceiverProfile.gold())


def test_short_write_is_a_protocol_failure() -> None:
    serial = FakeSerial(_success_responses(), short_write=True)
    receiver = Sa818SerialReceiver(serial_port=serial, settle_seconds=0)

    with pytest.raises(Sa818ProtocolError, match="short UART write"):
        receiver.configure(ReceiverProfile.gold())


def test_close_is_idempotent_and_closed_receiver_cannot_configure() -> None:
    serial = FakeSerial(_success_responses())
    receiver = Sa818SerialReceiver(serial_port=serial)

    receiver.close()
    receiver.close()

    assert serial.closes == 1
    with pytest.raises(RuntimeError, match="closed"):
        receiver.configure(ReceiverProfile.gold())

