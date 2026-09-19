from __future__ import annotations

from asm.domain.indicators import Indicator, IndicatorState


def test_only_creates_one_hot_state_for_every_indicator() -> None:
    for selected in Indicator:
        state = IndicatorState.only(selected)

        assert [indicator for indicator in Indicator if state.is_on(indicator)] == [selected]


def test_default_state_turns_every_indicator_off() -> None:
    state = IndicatorState()

    assert not any(state.is_on(indicator) for indicator in Indicator)

