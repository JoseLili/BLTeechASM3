"""Technology-neutral receiver configuration models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum, StrEnum


class ReceiverChannel(StrEnum):
    """Seven supported VHF weather-radio channels."""

    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"
    C5 = "C5"
    C6 = "C6"
    C7 = "C7"

    @property
    def frequency_mhz(self) -> Decimal:
        """Derive frequency from the channel so both values cannot diverge."""
        return _CHANNEL_FREQUENCIES[self]

    @property
    def frequency_text(self) -> str:
        """Return the four-decimal representation required by SA818 commands."""
        return f"{self.frequency_mhz:.4f}"


_CHANNEL_FREQUENCIES = {
    ReceiverChannel.C1: Decimal("162.4000"),
    ReceiverChannel.C2: Decimal("162.4250"),
    ReceiverChannel.C3: Decimal("162.4500"),
    ReceiverChannel.C4: Decimal("162.4750"),
    ReceiverChannel.C5: Decimal("162.5000"),
    ReceiverChannel.C6: Decimal("162.5250"),
    ReceiverChannel.C7: Decimal("162.5500"),
}


class ReceiverBandwidth(IntEnum):
    """Bandwidth values shared by the domain and SA818 protocol."""

    NARROW_12_5_KHZ = 0
    WIDE_25_KHZ = 1


class ReceiverFilter(IntEnum):
    """SA818 filter semantics: zero enables and one disables a filter."""

    ENABLED = 0
    DISABLED = 1


@dataclass(frozen=True, slots=True)
class ReceiverProfile:
    """Complete receive profile without any operation that can key PTT."""

    channel: ReceiverChannel
    bandwidth: ReceiverBandwidth = ReceiverBandwidth.WIDE_25_KHZ
    squelch: int = 0
    volume: int = 6
    pre_de_emphasis: ReceiverFilter = ReceiverFilter.ENABLED
    high_pass: ReceiverFilter = ReceiverFilter.ENABLED
    low_pass: ReceiverFilter = ReceiverFilter.ENABLED

    def __post_init__(self) -> None:
        if not 0 <= self.squelch <= 8:
            raise ValueError("squelch must be between 0 and 8")
        if not 1 <= self.volume <= 8:
            raise ValueError("volume must be between 1 and 8")

    @classmethod
    def gold(cls, channel: ReceiverChannel = ReceiverChannel.C7) -> ReceiverProfile:
        """Build the profile validated with real RWT messages on Carrier Rev A."""
        return cls(channel=channel)


@dataclass(frozen=True, slots=True)
class ReceiverConfigurationResult:
    """Verified receiver state and protocol evidence from one configuration."""

    model: str
    profile: ReceiverProfile
    responses: tuple[str, ...]
    verified: bool

