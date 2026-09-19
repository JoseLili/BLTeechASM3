from __future__ import annotations

from datetime import timedelta

import pytest

from asm.domain.indicators import Indicator
from asm.domain.same import (
    SameEndOfMessage,
    SameEventCode,
    SameNoticeReceipt,
    SameNoticeTracker,
    SameParseError,
    parse_multimon_same_line,
)

RWT_LINE = "EAS: ZCZC-CIV-RWT-000000+0300-832300-XDIF/005-"
EQW_LINE = "EAS: ZCZC-CIV-EQW-000000+0001-832300-XDIF/005-"


def _header(line: str):  # type: ignore[no-untyped-def]
    decoded = parse_multimon_same_line(line)
    assert decoded is not None and not isinstance(decoded, SameEndOfMessage)
    return decoded


def test_real_rwt_shape_accepts_all_units_and_opaque_metadata() -> None:
    header = _header(RWT_LINE)

    assert header.event is SameEventCode.RWT
    assert header.area_codes == ("000000",)
    assert header.applies_to_all_units is True
    assert header.validity == timedelta(hours=3)
    assert header.issued_code == "832300"
    assert header.sender == "XDIF/005"


def test_eqw_uses_one_minute_from_tttt() -> None:
    header = _header(EQW_LINE)

    assert header.event is SameEventCode.EQW
    assert header.validity == timedelta(minutes=1)


def test_multiple_six_digit_areas_remain_supported() -> None:
    header = _header("ZCZC-CIV-RWT-009000-015000+0300-1221200-XCMX/011-")

    assert header.area_codes == ("009000", "015000")
    assert header.applies_to_all_units is False


@pytest.mark.parametrize(
    "line",
    [
        "EAS: ZCZC-CIV-RWT-000000+0060-832300-XDIF/005-",
        "EAS: ZCZC-CIV-RWT-000000+0000-832300-XDIF/005-",
        "EAS: ZCZC-WXR-RWT-000000+0300-832300-XDIF/005-",
        "EAS: ZCZC-CIV-TOR-000000+0030-832300-XDIF/005-",
    ],
)
def test_unsupported_or_malformed_headers_fail_closed(line: str) -> None:
    with pytest.raises(SameParseError):
        parse_multimon_same_line(line)


def test_nnnn_is_framing_and_unrelated_output_is_ignored() -> None:
    assert isinstance(parse_multimon_same_line("EAS: NNNN"), SameEndOfMessage)
    assert parse_multimon_same_line("Enabled demodulators: EAS") is None


def test_tracker_blinks_rwt_and_does_not_extend_for_repetitions() -> None:
    tracker = SameNoticeTracker(
        blink_half_period_seconds=1.0,
        duplicate_window_seconds=10.0,
    )
    header = _header(RWT_LINE)

    assert tracker.receive(header, received_at=100.0) is SameNoticeReceipt.ACCEPTED
    assert tracker.snapshot(now=100.0).indicators.is_on(Indicator.ADVISORY)
    assert tracker.snapshot(now=101.0).phase_on is False
    assert tracker.receive(header, received_at=103.0) is SameNoticeReceipt.DUPLICATE
    assert tracker.snapshot(now=10_899.999).event is SameEventCode.RWT
    assert tracker.snapshot(now=10_900.0).event is None


def test_new_broadcast_after_duplicate_window_restarts_validity() -> None:
    tracker = SameNoticeTracker(
        blink_half_period_seconds=1.0,
        duplicate_window_seconds=10.0,
    )
    header = _header(RWT_LINE)
    tracker.receive(header, received_at=0.0)

    assert tracker.receive(header, received_at=10.001) is SameNoticeReceipt.ACCEPTED
    assert tracker.snapshot(now=10_810.0).event is SameEventCode.RWT


def test_eqw_overrides_rwt_then_unexpired_rwt_resumes() -> None:
    tracker = SameNoticeTracker(
        blink_half_period_seconds=1.0,
        duplicate_window_seconds=10.0,
    )
    tracker.receive(_header(RWT_LINE), received_at=0.0)
    tracker.receive(_header(EQW_LINE), received_at=30.0)

    eqw = tracker.snapshot(now=30.0)
    resumed_rwt = tracker.snapshot(now=90.0)

    assert eqw.event is SameEventCode.EQW
    assert eqw.indicators.is_on(Indicator.WARNING)
    assert resumed_rwt.event is SameEventCode.RWT
    assert resumed_rwt.indicators.is_on(Indicator.ADVISORY)
