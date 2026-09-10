"""RX-only SA818S-V adapter over its 9600 8N1 AT interface."""

from __future__ import annotations

import importlib
import time
from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from asm.domain.receiver import ReceiverConfigurationResult, ReceiverProfile


class SerialPort(Protocol):
    """Small pyserial-compatible surface used by the adapter and its fakes."""

    def reset_input_buffer(self) -> None: ...

    def write(self, data: bytes) -> int: ...

    def flush(self) -> None: ...

    def readline(self) -> bytes: ...

    def close(self) -> None: ...


class Sa818Error(RuntimeError):
    """Base class for actionable SA818 adapter failures."""


class Sa818TimeoutError(Sa818Error):
    """The module returned no response before the serial timeout."""


class Sa818ProtocolError(Sa818Error):
    """The module returned malformed or unexpected protocol data."""


class Sa818RejectedError(Sa818Error):
    """The module explicitly rejected a valid command."""


class Sa818VerificationError(Sa818Error):
    """Readback did not match the profile that was just applied."""


class Sa818SerialReceiver:
    """Configure and verify SA818S-V without exposing any transmit operation."""

    def __init__(
        self,
        *,
        serial_port: SerialPort,
        settle_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if settle_seconds < 0:
            raise ValueError("settle_seconds must not be negative")
        self._serial = serial_port
        self._settle_seconds = settle_seconds
        self._sleep = sleep
        self._settled = False
        self._closed = False

    @classmethod
    def open(
        cls,
        *,
        device: str = "/dev/serial0",
        timeout_seconds: float = 2.0,
        settle_seconds: float = 1.0,
    ) -> Self:
        """Open the Linux UART lazily so pure tests do not require pyserial."""
        if not device.strip():
            raise ValueError("device must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        try:
            serial_module = importlib.import_module("serial")
        except ImportError as error:
            raise RuntimeError(
                "SA818 support is unavailable. Install Debian package python3-serial."
            ) from error

        serial_port: SerialPort = serial_module.Serial(
            port=device,
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=timeout_seconds,
            write_timeout=timeout_seconds,
        )
        return cls(serial_port=serial_port, settle_seconds=settle_seconds)

    def configure(self, profile: ReceiverProfile) -> ReceiverConfigurationResult:
        """Apply the complete profile and require an exact group readback."""
        if self._closed:
            raise RuntimeError("SA818 serial receiver is closed")
        if not self._settled:
            self._sleep(self._settle_seconds)
            self._settled = True

        self._serial.reset_input_buffer()
        frequency = profile.channel.frequency_text
        group = (
            f"AT+DMOSETGROUP={int(profile.bandwidth)},{frequency},{frequency},"
            f"0000,{profile.squelch},0000"
        )
        filters = (
            f"AT+SETFILTER={int(profile.pre_de_emphasis)},"
            f"{int(profile.high_pass)},{int(profile.low_pass)}"
        )

        responses = (
            self._exchange("AT+DMOCONNECT", "+DMOCONNECT:0"),
            self._exchange(group, "+DMOSETGROUP:0"),
            self._exchange(f"AT+DMOSETVOLUME={profile.volume}", "+DMOSETVOLUME:0"),
            self._exchange(filters, "+DMOSETFILTER:0"),
        )
        readback = self._exchange_readback("AT+DMOREADGROUP")
        expected_readback = (
            f"+DMOREADGROUP:{int(profile.bandwidth)},{frequency},{frequency},"
            f"0000,{profile.squelch},0000"
        )
        if readback != expected_readback:
            raise Sa818VerificationError(
                f"SA818 readback mismatch: expected {expected_readback!r}, got {readback!r}"
            )

        return ReceiverConfigurationResult(
            model="SA818S-V",
            profile=profile,
            responses=(*responses, readback),
            verified=True,
        )

    def close(self) -> None:
        """Close the underlying UART exactly once."""
        if self._closed:
            return
        self._closed = True
        self._serial.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _exchange(self, command: str, expected: str) -> str:
        response = self._send_and_read(command)
        if response == expected:
            return response
        if response.startswith(expected.rsplit(":", maxsplit=1)[0] + ":"):
            raise Sa818RejectedError(f"SA818 rejected {command!r}: {response!r}")
        raise Sa818ProtocolError(f"unexpected response to {command!r}: {response!r}")

    def _exchange_readback(self, command: str) -> str:
        response = self._send_and_read(command)
        if not response.startswith("+DMOREADGROUP:"):
            raise Sa818ProtocolError(f"unexpected response to {command!r}: {response!r}")
        return response

    def _send_and_read(self, command: str) -> str:
        payload = f"{command}\r\n".encode("ascii")
        written = self._serial.write(payload)
        if written != len(payload):
            raise Sa818ProtocolError(
                f"short UART write for {command!r}: {written}/{len(payload)} bytes"
            )
        self._serial.flush()
        raw_response = self._serial.readline()
        if not raw_response:
            raise Sa818TimeoutError(f"SA818 did not answer {command!r}")
        try:
            response = raw_response.decode("ascii").strip()
        except UnicodeDecodeError as error:
            raise Sa818ProtocolError(f"non-ASCII response to {command!r}") from error
        if not response:
            raise Sa818ProtocolError(f"empty response to {command!r}")
        return response

