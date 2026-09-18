from asm.application.ports import DiagnosticView, MenuView, SystemView
from asm.domain.diagnostics import DiagnosticSeverity
from asm.domain.states import SystemState
from asm.infrastructure.display.null_display import NullDisplay
from asm.infrastructure.display.startup_animation import StartupFrame


def test_null_display_accepts_every_supported_view() -> None:
    display = NullDisplay()

    display.show(SystemView(state=SystemState.IDLE, title="Listo", detail="Escuchando"))
    display.show_menu(MenuView(title="Menu", items=("Estado",), selected_index=0))
    display.show_diagnostic(
        DiagnosticView(
            title="Audio",
            lines=("Sin pantalla",),
            severity=DiagnosticSeverity.WARNING,
        )
    )
    display.show_startup_frame(StartupFrame(progress=1.0, dots=0))
    display.clear()
