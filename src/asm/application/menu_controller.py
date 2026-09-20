"""Navigational controller for the local OLED menu.

The controller owns cursor and page history, but it neither changes hardware
nor persists settings. Leaf selections become actions for later use cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from asm.application.menu_input import MenuCommand
from asm.application.ports import MenuDisplayPort, MenuView


@dataclass(frozen=True, slots=True)
class MenuItem:
    """One selectable row, optionally opening a child page."""

    key: str
    label: str
    child: MenuPage | None = None

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.label.strip():
            raise ValueError("menu item key and label must not be empty")


@dataclass(frozen=True, slots=True)
class MenuPage:
    """Immutable menu page definition."""

    title: str
    items: tuple[MenuItem, ...]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("menu page title must not be empty")
        if not self.items:
            raise ValueError("menu page must contain at least one item")
        keys = [item.key for item in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("menu item keys must be unique within a page")


class MenuActionKind(StrEnum):
    """Actions that leave navigation and enter an application use case."""

    SELECT = "SELECT"
    TOGGLE_LISTEN = "TOGGLE_LISTEN"


@dataclass(frozen=True, slots=True)
class MenuAction:
    """Requested use case; target is present only for leaf selection."""

    kind: MenuActionKind
    target: str | None = None

    def __post_init__(self) -> None:
        if self.kind is MenuActionKind.SELECT and not (
            self.target and self.target.strip()
        ):
            raise ValueError("SELECT action requires a target")
        if self.kind is MenuActionKind.TOGGLE_LISTEN and self.target is not None:
            raise ValueError("TOGGLE_LISTEN action must not have a target")


@dataclass(slots=True)
class _Frame:
    page: MenuPage
    selected_index: int = 0


class MenuController:
    """Navigate an immutable tree and render every visible cursor change."""

    def __init__(self, *, display: MenuDisplayPort, root: MenuPage) -> None:
        self._display = display
        self._root = root
        self._stack: list[_Frame] = []

    @property
    def is_open(self) -> bool:
        return bool(self._stack)

    @property
    def current_view(self) -> MenuView | None:
        if not self._stack:
            return None
        frame = self._stack[-1]
        return MenuView(
            title=frame.page.title,
            items=tuple(item.label for item in frame.page.items),
            selected_index=frame.selected_index,
        )

    def open(self) -> MenuView:
        """Open at the root and render a deterministic initial selection."""
        self._stack = [_Frame(self._root)]
        return self._render()

    def close(self) -> None:
        """Close every page without rendering; the operational view resumes."""
        self._stack.clear()

    def refresh(self) -> MenuView:
        """Render the current page after a temporary application view closes."""
        if not self._stack:
            raise RuntimeError("cannot refresh a closed menu")
        return self._render()

    def handle(self, command: MenuCommand) -> MenuAction | None:
        """Apply one semantic command; closed menus ignore all input."""
        if command is MenuCommand.TOGGLE_LISTEN:
            return MenuAction(MenuActionKind.TOGGLE_LISTEN)
        if not self._stack:
            return None
        frame = self._stack[-1]

        if command is MenuCommand.MOVE_UP:
            frame.selected_index = (frame.selected_index - 1) % len(frame.page.items)
            self._render()
        elif command is MenuCommand.MOVE_DOWN:
            frame.selected_index = (frame.selected_index + 1) % len(frame.page.items)
            self._render()
        elif command in (MenuCommand.MOVE_LEFT, MenuCommand.GO_BACK):
            if len(self._stack) == 1:
                self._stack.clear()
            else:
                self._stack.pop()
                self._render()
        elif command in (MenuCommand.MOVE_RIGHT, MenuCommand.CONFIRM):
            selected = frame.page.items[frame.selected_index]
            if selected.child is not None:
                self._stack.append(_Frame(selected.child))
                self._render()
            else:
                return MenuAction(MenuActionKind.SELECT, selected.key)
        return None

    def _render(self) -> MenuView:
        view = self.current_view
        if view is None:  # pragma: no cover - protected by open/handle flow
            raise RuntimeError("cannot render a closed menu")
        self._display.show_menu(view)
        return view


DEFAULT_MENU = MenuPage(
    title="Menu principal",
    items=(
        MenuItem(
            key="receiver",
            label="Recepcion",
            child=MenuPage(
                title="Recepcion",
                items=(
                    MenuItem(key="receiver.channel", label="Canal C1-C7"),
                    MenuItem(key="receiver.status", label="Estado SA818"),
                ),
            ),
        ),
        MenuItem(
            key="audio",
            label="Audio",
            child=MenuPage(
                title="Audio",
                items=(
                    MenuItem(key="audio.listen", label="Escucha"),
                    MenuItem(key="audio.monitor_volume", label="Volumen monitor"),
                ),
            ),
        ),
        MenuItem(
            key="diagnostics",
            label="Diagnostico",
            child=MenuPage(
                title="Diagnostico",
                items=(
                    MenuItem(key="diagnostics.radio", label="Radio"),
                    MenuItem(key="diagnostics.audio", label="Audio"),
                    MenuItem(key="diagnostics.buttons", label="Botones"),
                    MenuItem(key="diagnostics.power", label="Energia"),
                ),
            ),
        ),
        MenuItem(
            key="system",
            label="Sistema",
            child=MenuPage(
                title="Sistema",
                items=(
                    MenuItem(key="system.site", label="Sitio"),
                    MenuItem(key="system.brightness", label="Brillo OLED"),
                ),
            ),
        ),
        MenuItem(
            key="information",
            label="Informacion",
            child=MenuPage(
                title="Informacion",
                items=(
                    MenuItem(key="information.version", label="Version"),
                    MenuItem(key="information.carrier", label="Carrier Rev A"),
                ),
            ),
        ),
    ),
)


PRODUCTION_MENU = MenuPage(
    title="Menu principal",
    items=(
        MenuItem(
            key="configuration",
            label="Configuracion",
            child=MenuPage(
                title="Configuracion",
                items=(
                    MenuItem(key="receiver.channel", label="Canal C1-C7"),
                    MenuItem(key="audio.alarm", label="Audio de alarma"),
                ),
            ),
        ),
        MenuItem(
            key="status",
            label="Estado equipo",
            child=MenuPage(
                title="Estado equipo",
                items=(
                    MenuItem(key="receiver.status", label="Receptor SA818"),
                    MenuItem(key="diagnostics.audio", label="Audio WM8960"),
                    MenuItem(key="diagnostics.rtc", label="Reloj HW-084"),
                    MenuItem(key="diagnostics.rwt", label="Recepcion RWT"),
                ),
            ),
        ),
        MenuItem(
            key="tests",
            label="Pruebas",
            child=MenuPage(
                title="Pruebas",
                items=(
                    MenuItem(key="tests.display", label="Pantalla OLED"),
                    MenuItem(key="tests.audio", label="Audio de salida"),
                    MenuItem(key="tests.buttons", label="Botones de menu"),
                ),
            ),
        ),
        MenuItem(
            key="information",
            label="Informacion",
            child=MenuPage(
                title="Informacion",
                items=(
                    MenuItem(key="information.version", label="Version software"),
                    MenuItem(key="information.carrier", label="Carrier v3.1 Rev A"),
                ),
            ),
        ),
    ),
)
