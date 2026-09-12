"""Continuous shell-free arecord, SoX, and multimon-ng SAME pipeline."""

from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass
from typing import BinaryIO, cast

from asm.application.ports import AudioHealthPort
from asm.config.models import AudioConfig
from asm.infrastructure.audio.errors import AudioProcessError, AudioUnavailableError


@dataclass(frozen=True, slots=True)
class SamePipelineCommands:
    capture: tuple[str, ...]
    convert: tuple[str, ...]
    decode: tuple[str, ...]


def build_same_pipeline_commands(config: AudioConfig) -> SamePipelineCommands:
    """Build the exact GOLD pipeline validated on Carrier v3.1 Rev A."""
    capture = config.capture_spec
    decoder = config.decoder_spec
    return SamePipelineCommands(
        capture=(
            "/usr/bin/arecord",
            "-q",
            "-D",
            config.pcm_device,
            "-t",
            "raw",
            "-f",
            capture.sample_format.value,
            "-r",
            str(capture.sample_rate_hz),
            "-c",
            str(capture.channels),
        ),
        convert=(
            "/usr/bin/sox",
            "-t",
            "raw",
            "-e",
            "signed-integer",
            "-b",
            "32",
            "-L",
            "-r",
            str(capture.sample_rate_hz),
            "-c",
            str(capture.channels),
            "-",
            "-t",
            "raw",
            "-e",
            "signed-integer",
            "-b",
            "16",
            "-L",
            "-r",
            str(decoder.sample_rate_hz),
            "-c",
            str(decoder.channels),
            "-",
            "remix",
            str(config.radio_capture_channel + 1),
        ),
        decode=("/usr/bin/multimon-ng", "-a", "EAS", "-t", "raw", "-"),
    )


class MultimonSameStream:
    """Own three child processes and expose decoded lines without blocking."""

    def __init__(self, *, config: AudioConfig, health: AudioHealthPort) -> None:
        self._config = config
        self._health = health
        self._processes: tuple[subprocess.Popen[bytes], ...] = ()
        self._output: BinaryIO | None = None
        self._buffer = bytearray()

    @property
    def is_running(self) -> bool:
        return bool(self._processes) and all(process.poll() is None for process in self._processes)

    def start(self) -> None:
        if self._processes:
            raise AudioProcessError("SAME decoder stream is already started")
        if not self._health.read().ready_for_capture:
            raise AudioUnavailableError("WM8960 capture or preload is unavailable")

        commands = build_same_pipeline_commands(self._config)
        started: list[subprocess.Popen[bytes]] = []
        try:
            capture = subprocess.Popen(
                commands.capture,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0,
            )
            started.append(capture)
            if capture.stdout is None:
                raise AudioProcessError("arecord stdout pipe was not created")
            convert = subprocess.Popen(
                commands.convert,
                stdin=capture.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0,
            )
            capture.stdout.close()
            started.append(convert)
            if convert.stdout is None:
                raise AudioProcessError("SoX stdout pipe was not created")
            decode = subprocess.Popen(
                commands.decode,
                stdin=convert.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
            )
            convert.stdout.close()
            started.append(decode)
            if decode.stdout is None:
                raise AudioProcessError("multimon-ng stdout pipe was not created")
            os.set_blocking(decode.stdout.fileno(), False)
        except (OSError, AudioProcessError) as error:
            _stop_processes(tuple(started))
            if isinstance(error, AudioProcessError):
                raise
            raise AudioProcessError(f"cannot start SAME decoder pipeline: {error}") from error

        self._processes = (capture, convert, decode)
        self._output = cast(BinaryIO, decode.stdout)
        self._buffer.clear()

    def poll_lines(self) -> tuple[str, ...]:
        if not self._processes or self._output is None:
            raise AudioProcessError("SAME decoder stream is not started")
        failed = [
            (name, process.returncode)
            for name, process in zip(
                ("arecord", "sox", "multimon-ng"), self._processes, strict=True
            )
            if process.poll() is not None
        ]
        if failed:
            name, status = failed[0]
            raise AudioProcessError(f"{name} exited with status {status}")

        while True:
            try:
                chunk = os.read(self._output.fileno(), 4096)
            except BlockingIOError:
                break
            except OSError as error:
                raise AudioProcessError(f"cannot read multimon-ng output: {error}") from error
            if not chunk:
                break
            self._buffer.extend(chunk)

        complete = self._buffer.split(b"\n")
        self._buffer = bytearray(complete.pop())
        return tuple(line.rstrip(b"\r").decode("utf-8", errors="replace") for line in complete)

    def stop(self) -> None:
        processes = self._processes
        self._processes = ()
        self._output = None
        self._buffer.clear()
        _stop_processes(processes)

    def close(self) -> None:
        self.stop()

    def __enter__(self) -> MultimonSameStream:
        self.start()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


def _stop_processes(processes: tuple[subprocess.Popen[bytes], ...]) -> None:
    for process in reversed(processes):
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
    for process in reversed(processes):
        if process.poll() is not None:
            continue
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
