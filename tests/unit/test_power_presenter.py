from __future__ import annotations

from asm.application.power_presenter import power_status_view
from asm.domain.power import PowerStatus, SignalState


def test_power_status_view_fits_all_five_semantic_inputs() -> None:
    view = power_status_view(
        PowerStatus(
            ac_ok=SignalState.ASSERTED,
            battery_disconnected=SignalState.CLEAR,
            battery_low=SignalState.UNKNOWN,
            battery_full=SignalState.ASSERTED,
            discharging=SignalState.CLEAR,
        )
    )

    assert view.title == "Energia - entradas"
    assert view.items == (
        "AC OK: SI",
        "Bat descon: NO",
        "Bat baja: ?",
        "Llena:SI UPS:NO",
    )
    assert all(len(item) <= 17 for item in view.items)
