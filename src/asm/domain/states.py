"""Domain states and events for the ASM state machine."""

from __future__ import annotations

from enum import StrEnum


class SystemState(StrEnum):
    """Operational states defined by the project architecture."""

    BOOT = "BOOT"
    SELF_TEST = "SELF_TEST"
    IDLE = "IDLE"
    TECH_MODE = "TECH_MODE"
    RWT_ACTIVE = "RWT_ACTIVE"
    SIMULACRO_ACTIVE = "SIMULACRO_ACTIVE"
    EVACUACION_ACTIVE = "EVACUACION_ACTIVE"
    EQW_ACTIVE = "EQW_ACTIVE"
    STOPPED = "STOPPED"
    RECEIVER_FAULT = "RECEIVER_FAULT"
    POWER_FAULT = "POWER_FAULT"
    MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED"


class EventType(StrEnum):
    """Operational inputs supported by the executable priority slice."""

    BOOT_COMPLETED = "BOOT_COMPLETED"
    SELF_TEST_PASSED = "SELF_TEST_PASSED"
    START_RWT = "START_RWT"
    START_SIMULACRO = "START_SIMULACRO"
    START_EVACUACION = "START_EVACUACION"
    START_EQW = "START_EQW"
    STOP_REQUESTED = "STOP_REQUESTED"


class EventSource(StrEnum):
    """Origin retained in audit evidence after semantic normalization."""

    SYSTEM = "SYSTEM"
    LOCAL_PANEL = "LOCAL_PANEL"
    RADIO = "RADIO"
