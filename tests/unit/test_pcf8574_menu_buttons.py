from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from asm.application.menu_input import MenuButton, MenuCommand
from asm.infrastructure.i2c.pcf8574_menu_buttons import (
    MENU_BUTTON_BITS,
    PCF8574_ADDRESS,
    PCF8574_INPUT_MASK,
    PCF8574_INTERRUPT_GPIO,
    Pcf8574MenuButtons,
)


@dataclass(slots=True)
class FakeBus:
    snapshots: list[int]
    writes: list[tuple[int, int]] = field(default_factory=list)
    reads: int = 0
    closed: bool = False

    def read_byte(self, _address: int) -> int:
        self.reads += 1
        return self.snapshots.pop(0)

    def write_byte(self, address: int, value: int) -> None:
        self.writes.append((address, value))

    def close(self) -> None:
        self.closed = True


@dataclass(slots=True)
class FakeInterrupt:
    when_pressed: Callable[[], None] | None = None
    closed: bool = False

    def trigger(self) -> None:
        assert self.when_pressed is not None
        self.when_pressed()

    def close(self) -> None:
        self.closed = True


def _panel(
    snapshots: list[int],
    observed: list[MenuCommand],
    *,
    owns_bus: bool = False,
) -> tuple[Pcf8574MenuButtons, FakeBus, FakeInterrupt]:
    bus = FakeBus(snapshots=snapshots)
    interrupt = FakeInterrupt()
    panel = Pcf8574MenuButtons(
        bus=bus,
        interrupt=interrupt,
        on_command=observed.append,
        owns_bus=owns_bus,
    )
    return panel, bus, interrupt


def test_frozen_mapping_matches_carrier_revision_a() -> None:
    assert [(mapping.button, mapping.bit) for mapping in MENU_BUTTON_BITS] == [
        (MenuButton.UP, 0),
        (MenuButton.DOWN, 1),
        (MenuButton.LEFT, 2),
        (MenuButton.RIGHT, 3),
        (MenuButton.ENTER, 4),
        (MenuButton.BACK, 5),
        (MenuButton.LISTEN, 6),
    ]
    assert PCF8574_ADDRESS == 0x20
    assert PCF8574_INTERRUPT_GPIO == 16


def test_initialization_releases_all_ports_and_establishes_baseline() -> None:
    panel, bus, _interrupt = _panel([0xFF], [])

    assert bus.writes == [(PCF8574_ADDRESS, PCF8574_INPUT_MASK)]
    assert bus.reads == 1
    panel.close()


def test_interrupt_callback_defers_i2c_until_poll() -> None:
    observed: list[MenuCommand] = []
    panel, bus, interrupt = _panel([0xFF, 0xFE], observed)

    interrupt.trigger()
    assert bus.reads == 1
    assert observed == []

    assert panel.poll() == (MenuCommand.MOVE_UP,)
    assert observed == [MenuCommand.MOVE_UP]
    assert bus.reads == 2
    panel.close()


def test_press_emits_once_until_release_and_repress() -> None:
    observed: list[MenuCommand] = []
    panel, _bus, interrupt = _panel([0xFF, 0xFE, 0xFE, 0xFF, 0xFE], observed)

    for _snapshot in range(4):
        interrupt.trigger()
        panel.poll()

    assert observed == [MenuCommand.MOVE_UP, MenuCommand.MOVE_UP]
    panel.close()


def test_simultaneous_buttons_are_emitted_in_port_order_and_p7_is_ignored() -> None:
    observed: list[MenuCommand] = []
    # P0, P4, P6 and reserved P7 transition LOW together.
    panel, _bus, interrupt = _panel([0xFF, 0x2E], observed)

    interrupt.trigger()
    assert panel.poll() == (
        MenuCommand.MOVE_UP,
        MenuCommand.CONFIRM,
        MenuCommand.TOGGLE_LISTEN,
    )
    panel.close()


def test_close_releases_owned_resources_and_is_idempotent() -> None:
    panel, bus, interrupt = _panel([0xFF], [], owns_bus=True)

    panel.close()
    panel.close()

    assert interrupt.closed is True
    assert interrupt.when_pressed is None
    assert bus.closed is True
