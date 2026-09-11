from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from asm.application.ports import DiagnosticView, MenuView, SystemView
from asm.config import DEFAULT_CONFIG
from asm.domain.diagnostics import DiagnosticSeverity
from asm.domain.states import SystemState
from asm.infrastructure.display.luma_oled import LumaOledDisplay, _fit, _waveform_prefix
from asm.infrastructure.display.startup_animation import StartupFrame


@dataclass(slots=True)
class FakeDevice:
    bounding_box: tuple[int, int, int, int] = (0, 0, 127, 63)
    cleared: bool = False

    def clear(self) -> None:
        self.cleared = True


@dataclass(slots=True)
class FakeDrawingSurface:
    operations: list[tuple[str, tuple[object, ...]]] = field(default_factory=list)

    def rectangle(self, xy: object, *, outline: str, fill: str) -> None:
        self.operations.append(("rectangle", (xy, outline, fill)))

    def line(self, xy: object, *, fill: str) -> None:
        self.operations.append(("line", (xy, fill)))

    def text(self, xy: object, text: str, *, fill: str) -> None:
        self.operations.append(("text", (xy, text, fill)))


def test_oled_adapter_renders_boot_view_and_clears() -> None:
    device = FakeDevice()
    drawing = FakeDrawingSurface()

    @contextmanager
    def canvas_factory(_device: object) -> Iterator[FakeDrawingSurface]:
        yield drawing

    display = LumaOledDisplay(
        device=device,
        canvas_factory=canvas_factory,
        branding=DEFAULT_CONFIG.branding,
    )
    display.show(
        SystemView(
            state=SystemState.BOOT,
            title="ASM BLTeech",
            detail="Iniciando",
        )
    )
    display.clear()

    text_values = [payload[1] for name, payload in drawing.operations if name == "text"]
    assert text_values == ["ASM BLTeech", "Iniciando", "Estado: BOOT"]
    assert drawing.operations[0][0] == "rectangle"
    assert device.cleared is True


def test_fit_normalizes_and_truncates_long_text() -> None:
    assert _fit("  Sistema    listo  ") == "Sistema listo"
    assert _fit("x" * 21) == f"{'x' * 19}…"


def test_oled_adapter_renders_branded_startup_frame() -> None:
    device = FakeDevice()
    drawing = FakeDrawingSurface()

    @contextmanager
    def canvas_factory(_device: object) -> Iterator[FakeDrawingSurface]:
        yield drawing

    display = LumaOledDisplay(
        device=device,
        canvas_factory=canvas_factory,
        branding=DEFAULT_CONFIG.branding,
    )
    display.show_startup_frame(StartupFrame(progress=1.0, dots=3))

    text_values = [payload[1] for name, payload in drawing.operations if name == "text"]
    assert text_values == ["BLTeech", "ASM v3", "Iniciando..."]
    assert any(name == "line" for name, _payload in drawing.operations)
    assert _waveform_prefix(1.0)[-1] == (121, 29)


def test_oled_adapter_renders_scrolling_menu_and_selected_marker() -> None:
    device = FakeDevice()
    drawing = FakeDrawingSurface()

    @contextmanager
    def canvas_factory(_device: object) -> Iterator[FakeDrawingSurface]:
        yield drawing

    display = LumaOledDisplay(
        device=device,
        canvas_factory=canvas_factory,
        branding=DEFAULT_CONFIG.branding,
    )
    display.show_menu(
        MenuView(
            title="Menu principal",
            items=("Recepcion", "Audio", "Diagnostico", "Sistema", "Informacion"),
            selected_index=4,
        )
    )

    text_values = [payload[1] for name, payload in drawing.operations if name == "text"]
    assert text_values == [
        "Menu principal",
        " Audio",
        " Diagnostico",
        " Sistema",
        ">Informacion",
    ]


def test_oled_adapter_renders_diagnostic_notice() -> None:
    device = FakeDevice()
    drawing = FakeDrawingSurface()

    @contextmanager
    def canvas_factory(_device: object) -> Iterator[FakeDrawingSurface]:
        yield drawing

    display = LumaOledDisplay(
        device=device,
        canvas_factory=canvas_factory,
        branding=DEFAULT_CONFIG.branding,
    )
    display.show_diagnostic(
        DiagnosticView(
            title="Aviso de energia",
            lines=("Red CA disponible: NO", "Operacion en bateria: SI"),
            severity=DiagnosticSeverity.INFO,
        )
    )

    text_values = [payload[1] for name, payload in drawing.operations if name == "text"]
    assert text_values == [
        "Aviso de energia",
        "INFO",
        "Red CA disponible: …",
        "Operacion en bateri…",
    ]
