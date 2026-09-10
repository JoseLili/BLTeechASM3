"""Technology-neutral ports used by application services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from asm.domain.indicators import IndicatorState
from asm.domain.models import AuditRecord
from asm.domain.power import PowerStatus
from asm.domain.receiver import ReceiverChannel, ReceiverConfigurationResult, ReceiverProfile
from asm.domain.states import SystemState


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


class ClockPort(Protocol):
    """Provide civil time without coupling the application to the system clock."""

    def now(self) -> datetime: ...


class DisplayPort(Protocol):
    """Present semantic system information on any display adapter."""

    def show(self, view: SystemView) -> None: ...


class MenuDisplayPort(Protocol):
    """Present complete menu pages independently from operational states."""

    def show_menu(self, view: MenuView) -> None: ...


class EventLogRepository(Protocol):
    """Persist audit records in append-only order."""

    def append(self, record: AuditRecord) -> None: ...


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


class IndicatorPort(Protocol):
    """Apply a complete semantic state to every panel indicator."""

    def apply(self, state: IndicatorState) -> None: ...
