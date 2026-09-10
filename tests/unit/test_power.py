from __future__ import annotations

from asm.domain.power import PowerSignal, PowerStatus, SignalState


def test_status_exposes_asserted_signals_without_assigning_severity() -> None:
    status = PowerStatus(
        ac_ok=SignalState.ASSERTED,
        battery_disconnected=SignalState.CLEAR,
        battery_low=SignalState.ASSERTED,
        battery_full=SignalState.CLEAR,
        discharging=SignalState.UNKNOWN,
    )

    assert status.state_for(PowerSignal.AC_OK) is SignalState.ASSERTED
    assert status.asserted_signals == (PowerSignal.AC_OK, PowerSignal.BATTERY_LOW)
    assert status.is_complete is False


def test_status_is_complete_when_every_signal_is_binary() -> None:
    status = PowerStatus(
        ac_ok=SignalState.CLEAR,
        battery_disconnected=SignalState.CLEAR,
        battery_low=SignalState.CLEAR,
        battery_full=SignalState.CLEAR,
        discharging=SignalState.CLEAR,
    )

    assert status.is_complete is True

