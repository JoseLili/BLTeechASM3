from __future__ import annotations

import pytest

from asm.application.indicator_policy import indicator_state_for
from asm.domain.indicators import Indicator
from asm.domain.states import SystemState


@pytest.mark.parametrize("state", list(SystemState))
def test_power_indicator_is_on_for_every_controlled_state(state: SystemState) -> None:
    assert indicator_state_for(state).is_on(Indicator.POWER)


@pytest.mark.parametrize(
    ("state", "indicator"),
    [
        (SystemState.RWT_ACTIVE, Indicator.ADVISORY),
        (SystemState.SIMULACRO_ACTIVE, Indicator.WATCH),
        (SystemState.EVACUACION_ACTIVE, Indicator.WATCH),
        (SystemState.EQW_ACTIVE, Indicator.WARNING),
        (SystemState.RECEIVER_FAULT, Indicator.WARNING),
        (SystemState.POWER_FAULT, Indicator.WARNING),
        (SystemState.MAINTENANCE_REQUIRED, Indicator.WARNING),
    ],
)
def test_active_states_select_the_expected_event_indicator(
    state: SystemState, indicator: Indicator
) -> None:
    panel = indicator_state_for(state)
    event_indicators = (Indicator.ADVISORY, Indicator.WATCH, Indicator.WARNING)

    assert panel.is_on(indicator)
    assert sum(panel.is_on(candidate) for candidate in event_indicators) == 1


@pytest.mark.parametrize(
    "state",
    [
        SystemState.BOOT,
        SystemState.SELF_TEST,
        SystemState.IDLE,
        SystemState.TECH_MODE,
        SystemState.STOPPED,
    ],
)
def test_non_event_states_leave_event_indicators_off(state: SystemState) -> None:
    panel = indicator_state_for(state)
    assert panel.advisory is panel.watch is panel.warning is False
