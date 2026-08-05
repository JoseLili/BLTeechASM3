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
    """Inputs supported by the first executable state-machine slice."""

    BOOT_COMPLETED = "BOOT_COMPLETED"
    SELF_TEST_PASSED = "SELF_TEST_PASSED"
    START_SIMULACRO = "START_SIMULACRO"
    STOP_REQUESTED = "STOP_REQUESTED"
