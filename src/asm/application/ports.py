"""Technology-neutral ports used by application services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from asm.domain.audio import AudioDeviceStatus
from asm.domain.diagnostics import DiagnosticRecord, DiagnosticSeverity
from asm.domain.indicators import IndicatorState
from asm.domain.models import AuditRecord
from asm.domain.power import PowerStatus
from asm.domain.receiver import ReceiverChannel, ReceiverConfigurationResult, ReceiverProfile
from asm.domain.states import EventType, SystemState


@dataclass(frozen=True, slots=True)
class SystemView:
    """Semantic content to present on a display."""

    state: SystemState
    title: str
    detail: str


@dataclass(frozen=True, slots=True)
class MenuView:
    """One menu page rendered without exposing display technology."""

    title: str
    items: tuple[str, ...]
    selected_index: int

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("menu title must not be empty")
        if not self.items:
            raise ValueError("menu must contain at least one item")
        if not 0 <= self.selected_index < len(self.items):
            raise ValueError("selected_index must reference a menu item")


@dataclass(frozen=True, slots=True)
class DiagnosticView:
    """Short-lived diagnostic notice suitable for the 128x64 OLED."""

    title: str
    lines: tuple[str, ...]
    severity: DiagnosticSeverity

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("diagnostic title must not be empty")
        if not 1 <= len(self.lines) <= 3:
            raise ValueError("diagnostic view must contain between one and three lines")
        if any(not line.strip() for line in self.lines):
            raise ValueError("diagnostic lines must not be empty")


class ClockPort(Protocol):
    """Provide civil time without coupling the application to the system clock."""

    def now(self) -> datetime: ...


class DisplayPort(Protocol):
    """Present semantic system information on any display adapter."""

    def show(self, view: SystemView) -> None: ...


class MenuDisplayPort(Protocol):
    """Present complete menu pages independently from operational states."""

    def show_menu(self, view: MenuView) -> None: ...


class DiagnosticDisplayPort(Protocol):
    """Present an asynchronous diagnostic notice."""

    def show_diagnostic(self, view: DiagnosticView) -> None: ...


class EventLogRepository(Protocol):
    """Persist audit records in append-only order."""

    def append(self, record: AuditRecord) -> None: ...


class DiagnosticLogRepository(Protocol):
    """Persist hardware diagnostic records in append-only order."""

    def append(self, record: DiagnosticRecord) -> None: ...


class ReceiverPort(Protocol):
    """Configure and verify a receiver without exposing its hardware protocol."""

    def configure(self, profile: ReceiverProfile) -> ReceiverConfigurationResult: ...


class ReceiverChannelRepository(Protocol):
    """Load and atomically save the last confirmed receiver channel."""

    def load(self) -> ReceiverChannel | None: ...

    def save(self, channel: ReceiverChannel) -> None: ...


class PowerMonitorPort(Protocol):
    """Read semantic Mean Well states without exposing optos or GPIO levels."""

    def read(self) -> PowerStatus: ...


class AudioHealthPort(Protocol):
    """Read ALSA and preload readiness without opening an audio stream."""

    def read(self) -> AudioDeviceStatus: ...


class AudioPlaybackPort(Protocol):
    """Start and interrupt one audio asset without exposing ALSA."""

    @property
    def is_playing(self) -> bool: ...

    def start(self, asset: Path) -> None: ...

    def stop(self) -> None: ...


class EventAudioPort(Protocol):
    """Play one priority-controlled WAV for an operational event."""

    def play(self, event: EventType) -> bool: ...

    def poll(self) -> None: ...

    def stop(self) -> None: ...


class SameDecoderStreamPort(Protocol):
    """Own the external audio decoder pipeline behind a nonblocking API."""

    def start(self) -> None: ...

    def poll_lines(self) -> tuple[str, ...]: ...

    def stop(self) -> None: ...


class IndicatorPort(Protocol):
    """Apply a complete semantic state to every panel indicator."""

    def apply(self, state: IndicatorState) -> None: ...
