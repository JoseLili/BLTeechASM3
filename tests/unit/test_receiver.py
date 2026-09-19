from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from asm.domain.receiver import ReceiverChannel, ReceiverProfile


def test_all_channels_derive_the_frozen_frequency_map() -> None:
    assert [(channel.value, channel.frequency_mhz) for channel in ReceiverChannel] == [
        ("C1", Decimal("162.4000")),
        ("C2", Decimal("162.4250")),
        ("C3", Decimal("162.4500")),
        ("C4", Decimal("162.4750")),
        ("C5", Decimal("162.5000")),
        ("C6", Decimal("162.5250")),
        ("C7", Decimal("162.5500")),
    ]


def test_gold_profile_matches_carrier_revision_a_contract() -> None:
    profile = ReceiverProfile.gold()

    assert profile.channel is ReceiverChannel.C7
    assert profile.channel.frequency_text == "162.5500"
    assert int(profile.bandwidth) == 1
    assert profile.squelch == 0
    assert profile.volume == 6
    assert int(profile.pre_de_emphasis) == 0
    assert int(profile.high_pass) == 0
    assert int(profile.low_pass) == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [("squelch", -1), ("squelch", 9), ("volume", 0), ("volume", 9)],
)
def test_profile_rejects_out_of_range_settings(field: str, value: int) -> None:
    with pytest.raises(ValueError):
        replace(ReceiverProfile.gold(), **{field: value})
