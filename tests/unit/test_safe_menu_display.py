from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from asm.application.ports import MenuView
from asm.application.safe_menu_display import SafeMenuDisplay


@dataclass
class FakeMessages:
    requests: list[tuple[str, MenuView, float]] = field(default_factory=list)

    def request_menu_view(
        self,
        *,
        key: str,
        view: MenuView,
        duration_seconds: float,
    ) -> bool:
        self.requests.append((key, view, duration_seconds))
        return True


def test_menu_page_is_queued_with_content_derived_key() -> None:
    messages = FakeMessages()
    adapter = SafeMenuDisplay(messages=messages, duration_seconds=10.0)  # type: ignore[arg-type]
    view = MenuView(title="Menu", items=("A", "B"), selected_index=1)

    adapter.show_menu(view)

    assert messages.requests == [("Menu:1:A:B", view, 10.0)]


def test_timeout_must_be_positive() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        SafeMenuDisplay(messages=FakeMessages(), duration_seconds=0)  # type: ignore[arg-type]
