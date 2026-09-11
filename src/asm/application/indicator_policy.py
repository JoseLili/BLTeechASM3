"""Single state-to-indicator policy for the Carrier Rev A panel."""

from __future__ import annotations

from asm.domain.indicators import IndicatorState
from asm.domain.states import SystemState


def indicator_state_for(state: SystemState) -> IndicatorState:
    """Derive all four outputs from one operational state.

    POWER indicates that the application is controlling the panel. The three
    event lamps are mutually exclusive in this first policy revision.
    """
    return IndicatorState(
        advisory=state is SystemState.RWT_ACTIVE,
        watch=state in (SystemState.SIMULACRO_ACTIVE, SystemState.EVACUACION_ACTIVE),
        warning=state
        in (
            SystemState.EQW_ACTIVE,
            SystemState.RECEIVER_FAULT,
            SystemState.POWER_FAULT,
            SystemState.MAINTENANCE_REQUIRED,
        ),
        power=True,
    )
