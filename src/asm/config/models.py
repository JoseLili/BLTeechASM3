"""Typed and immutable application configuration models.

Configuration holds installation and presentation choices. Safety rules such
as event priorities and valid state transitions deliberately do not belong
here, because they must not change through an operator-edited file.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from asm.domain.audio import AudioStreamSpec, PcmSampleFormat
from asm.domain.receiver import ReceiverChannel


def _required_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class BrandingConfig:
    """Names and labels used to identify BLTeech and this product generation."""

    company_name: str
    product_name: str
    generation: str
    startup_text: str

    def __post_init__(self) -> None:
        _required_text(self.company_name, "company_name")
        _required_text(self.product_name, "product_name")
        _required_text(self.generation, "generation")
        _required_text(self.startup_text, "startup_text")


@dataclass(frozen=True, slots=True)
class DisplayConfig:
    """Non-critical timing choices for the local display."""

    startup_animation_seconds: float
    rwt_notice_seconds: float

    def __post_init__(self) -> None:
        if not 0 < self.startup_animation_seconds <= 10:
            raise ValueError("startup_animation_seconds must be greater than zero and at most 10")
        if not 1 <= self.rwt_notice_seconds <= 30:
            raise ValueError("rwt_notice_seconds must be between 1 and 30")


class ActivationMode(StrEnum):
    """Operator-selectable activation behavior for non-emergency buttons."""

    IMMEDIATE = "IMMEDIATE"
    HOLD = "HOLD"


@dataclass(frozen=True, slots=True)
class ConfigurableButtonAction:
    """Activation policy available only to Simulacro and Evacuación."""

    mode: ActivationMode
    hold_seconds: float

    def __post_init__(self) -> None:
        if not 0 < self.hold_seconds <= 10:
            raise ValueError("hold_seconds must be greater than zero and at most 10")


@dataclass(frozen=True, slots=True)
class ButtonInputConfig:
    """Electrical filtering shared by the three physical panel buttons."""

    debounce_seconds: float
    simulacro: ConfigurableButtonAction
    evacuacion: ConfigurableButtonAction

    def __post_init__(self) -> None:
        if not 0 < self.debounce_seconds <= 0.2:
            raise ValueError("debounce_seconds must be greater than zero and at most 0.2")


@dataclass(frozen=True, slots=True)
class MenuButtonInputConfig:
    """Electrical filtering for the dedicated PCF8574 menu keypad interrupt."""

    debounce_seconds: float

    def __post_init__(self) -> None:
        if not 0 < self.debounce_seconds <= 0.2:
            raise ValueError("debounce_seconds must be greater than zero and at most 0.2")


@dataclass(frozen=True, slots=True)
class PowerMonitoringConfig:
    """Stability window before publishing a Mean Well input change."""

    debounce_seconds: float

    def __post_init__(self) -> None:
        if not 0 < self.debounce_seconds <= 5:
            raise ValueError("debounce_seconds must be greater than zero and at most 5")


@dataclass(frozen=True, slots=True)
class AudioConfig:
    """Validated ALSA identity and PCM contract for Carrier v3.1 Rev A."""

    card_name: str
    pcm_device: str
    preload_service: str
    capture_spec: AudioStreamSpec
    decoder_spec: AudioStreamSpec
    radio_capture_channel: int

    def __post_init__(self) -> None:
        _required_text(self.card_name, "card_name")
        _required_text(self.pcm_device, "pcm_device")
        _required_text(self.preload_service, "preload_service")
        if self.decoder_spec.channels != 1:
            raise ValueError("decoder_spec must be mono")
        if not 0 <= self.radio_capture_channel < self.capture_spec.channels:
            raise ValueError("radio_capture_channel must reference a capture channel")

    @classmethod
    def wm8960(cls) -> AudioConfig:
        return cls(
            card_name="wm8960soundcard",
            pcm_device="hw:wm8960soundcard,0",
            preload_service="wm8960-audio-board-preload.service",
            capture_spec=AudioStreamSpec(PcmSampleFormat.S32_LE, 48_000, 2),
            decoder_spec=AudioStreamSpec(PcmSampleFormat.S16_LE, 22_050, 1),
            radio_capture_channel=1,
        )


@dataclass(frozen=True, slots=True)
class ReceiverConfig:
    """Startup channel and Linux UART timing for the installed receiver."""

    channel: ReceiverChannel
    serial_device: str
    command_timeout_seconds: float
    startup_settle_seconds: float

    def __post_init__(self) -> None:
        _required_text(self.serial_device, "serial_device")
        if not 0 < self.command_timeout_seconds <= 10:
            raise ValueError("command_timeout_seconds must be greater than zero and at most 10")
        if not 0 <= self.startup_settle_seconds <= 10:
            raise ValueError("startup_settle_seconds must be between zero and 10")


@dataclass(frozen=True, slots=True)
class SystemConfig:
    """Root object passed explicitly to application composition code."""

    branding: BrandingConfig
    display: DisplayConfig
    buttons: ButtonInputConfig
    menu_buttons: MenuButtonInputConfig
    power_monitoring: PowerMonitoringConfig
    audio: AudioConfig
    receiver: ReceiverConfig
