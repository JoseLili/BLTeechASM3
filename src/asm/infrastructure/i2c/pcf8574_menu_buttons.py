"""PCF8574P adapter for the seven dedicated menu buttons.

The expander is quasi-bidirectional, so all port bits are written HIGH before
reading them as inputs. Its active-low INT callback only marks work pending;
I2C access happens later in :meth:`poll`, outside gpiozero's callback thread.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Event, Lock
from typing import Protocol, Self

from asm.application.menu_input import MenuButton, MenuCommand, command_for_menu_button

PCF8574_ADDRESS = 0x20
PCF8574_INTERRUPT_GPIO = 16
PCF8574_INPUT_MASK = 0xFF


class ByteBus(Protocol):
    """Minimal SMBus surface used by this adapter."""

    def read_byte(self, address: int) -> int: ...

    def write_byte(self, address: int, value: int) -> None: ...

    def close(self) -> None: ...


class InterruptInput(Protocol):
    """Minimal gpiozero-compatible interrupt input."""

    when_pressed: Callable[[], None] | None

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class MenuButtonBit:
    """Frozen carrier mapping from one PCF8574 port bit to a button."""

    button: MenuButton
    bit: int


MENU_BUTTON_BITS = (
    MenuButtonBit(MenuButton.UP, 0),
    MenuButtonBit(MenuButton.DOWN, 1),
    MenuButtonBit(MenuButton.LEFT, 2),
    MenuButtonBit(MenuButton.RIGHT, 3),
    MenuButtonBit(MenuButton.ENTER, 4),
    MenuButtonBit(MenuButton.BACK, 5),
    MenuButtonBit(MenuButton.LISTEN, 6),
)


class Pcf8574MenuButtons:
    """Convert active-low PCF8574 snapshots into one command per press."""

    def __init__(
        self,
        *,
        bus: ByteBus,
        interrupt: InterruptInput,
        on_command: Callable[[MenuCommand], None],
        address: int = PCF8574_ADDRESS,
        owns_bus: bool = False,
    ) -> None:
        if not 0x03 <= address <= 0x77:
            raise ValueError("address must be a valid 7-bit I2C device address")

        self._bus = bus
        self._interrupt = interrupt
        self._on_command = on_command
        self._address = address
        self._owns_bus = owns_bus
        self._pending = Event()
        self._lock = Lock()
        self._closed = False

        # PCF8574 inputs are obtained by releasing their quasi-bidirectional
        # outputs HIGH. Reading once also establishes an edge-free baseline.
        self._bus.write_byte(self._address, PCF8574_INPUT_MASK)
        self._last_snapshot = self._read_snapshot()
        self._interrupt.when_pressed = self._mark_pending

    @classmethod
    def open(
        cls,
        *,
        on_command: Callable[[MenuCommand], None],
        bus_number: int = 1,
        address: int = PCF8574_ADDRESS,
        interrupt_gpio: int = PCF8574_INTERRUPT_GPIO,
        debounce_seconds: float = 0.05,
    ) -> Self:
        """Open the validated carrier devices on Raspberry Pi."""
        try:
            from gpiozero import Button  # type: ignore[import-not-found]
            from smbus2 import SMBus  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError(
                "PCF8574 menu support requires gpiozero and smbus2"
            ) from error

        bus = SMBus(bus_number)
        try:
            interrupt = Button(
                pin=interrupt_gpio,
                pull_up=True,
                bounce_time=debounce_seconds,
            )
            return cls(
                bus=bus,
                interrupt=interrupt,
                on_command=on_command,
                address=address,
                owns_bus=True,
            )
        except Exception:
            bus.close()
            raise

    def poll(self, *, force: bool = False) -> tuple[MenuCommand, ...]:
        """Read a pending snapshot and emit newly pressed buttons in P0-P6 order."""
        if not force and not self._pending.is_set():
            return ()

        with self._lock:
            if self._closed:
                return ()
            # Clear before reading so an interrupt arriving during I2C access
            # remains pending for the next application-loop iteration.
            self._pending.clear()
            snapshot = self._read_snapshot()
            falling_bits = self._last_snapshot & ~snapshot & PCF8574_INPUT_MASK
            self._last_snapshot = snapshot

        commands = tuple(
            command_for_menu_button(mapping.button)
            for mapping in MENU_BUTTON_BITS
            if falling_bits & (1 << mapping.bit)
        )
        for command in commands:
            self._on_command(command)
        return commands

    @property
    def read_pending(self) -> bool:
        """Report an interrupt without performing any I2C transaction."""
        return self._pending.is_set() and not self._closed

    def close(self) -> None:
        """Detach callbacks and release GPIO/I2C resources owned by the adapter."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._interrupt.when_pressed = None
            self._interrupt.close()
            if self._owns_bus:
                self._bus.close()

    def _mark_pending(self) -> None:
        self._pending.set()

    def _read_snapshot(self) -> int:
        snapshot = self._bus.read_byte(self._address)
        if not 0 <= snapshot <= PCF8574_INPUT_MASK:
            raise ValueError("PCF8574 snapshot must be one byte")
        return snapshot
