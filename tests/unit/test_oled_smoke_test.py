from __future__ import annotations

import argparse

import pytest

from scripts.oled_smoke_test import _parser, _positive_seconds


def test_oled_defaults_match_validated_carrier_inventory() -> None:
    args = _parser().parse_args([])

    assert args.bus == 1
    assert args.address == 0x3C
    assert args.seconds == 10.0


def test_oled_address_accepts_hexadecimal_override() -> None:
    args = _parser().parse_args(["--address", "0x3D"])

    assert args.address == 0x3D


def test_duration_must_be_positive() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _positive_seconds("0")
