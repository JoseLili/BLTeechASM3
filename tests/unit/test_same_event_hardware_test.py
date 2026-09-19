from __future__ import annotations

import argparse

import pytest

from scripts.same_event_hardware_test import _bounded_seconds, _parser


def test_eqw_is_the_bounded_hardware_test_default() -> None:
    args = _parser().parse_args([])

    assert args.event == "EQW"
    assert args.seconds == 15.0
    assert args.diagnostic_log.as_posix() == "/tmp/asm-same-hardware-test.jsonl"


@pytest.mark.parametrize("value", ["0", "0.99", "60.01"])
def test_hardware_test_rejects_unsafe_duration(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _bounded_seconds(value)
