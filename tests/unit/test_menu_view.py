from __future__ import annotations

import pytest

from asm.application.ports import MenuView


def test_menu_view_rejects_selection_outside_items() -> None:
    with pytest.raises(ValueError, match="selected_index"):
        MenuView(title="Menu", items=("Uno",), selected_index=1)


def test_menu_view_rejects_empty_content() -> None:
    with pytest.raises(ValueError, match="title"):
        MenuView(title=" ", items=("Uno",), selected_index=0)
    with pytest.raises(ValueError, match="at least one"):
        MenuView(title="Menu", items=(), selected_index=0)
