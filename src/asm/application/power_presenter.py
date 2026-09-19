"""OLED presentation for a semantic Mean Well power snapshot."""

from __future__ import annotations

from asm.application.ports import MenuView
from asm.domain.power import PowerStatus, SignalState

_SHORT_STATE = {
    SignalState.ASSERTED: "SI",
    SignalState.CLEAR: "NO",
    SignalState.UNKNOWN: "?",
}


def power_status_view(status: PowerStatus) -> MenuView:
    """Fit all five signal assertions into one 128x64 diagnostic page."""
    state = _SHORT_STATE.__getitem__
    return MenuView(
        title="Energia - entradas",
        items=(
            f"AC OK: {state(status.ac_ok)}",
            f"Bat descon: {state(status.battery_disconnected)}",
            f"Bat baja: {state(status.battery_low)}",
            (
                f"Llena:{state(status.battery_full)} "
                f"UPS:{state(status.discharging)}"
            ),
        ),
        selected_index=0,
    )
