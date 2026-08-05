"""Validate all three debounced carrier buttons in one diagnostic session."""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from threading import Event, Lock
from typing import Protocol

from asm.config import DEFAULT_CONFIG
from asm.infrastructure.gpio.levels import active_low_level


@dataclass(frozen=True, slots=True)
class ButtonSpec:
    """Expected physical mapping for one carrier button."""

    name: str
    gpio: int


BUTTONS = (
    ButtonSpec(name="Simulacro", gpio=17),
    ButtonSpec(name="Paro", gpio=27),
    ButtonSpec(name="Evacuacion", gpio=22),
)


class DiagnosticButton(Protocol):
    """gpiozero operations used by this diagnostic and no others."""

    is_pressed: bool
    when_pressed: Callable[[], None] | None
    when_released: Callable[[], None] | None

    def close(self) -> None: ...


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="maximum time to complete one cycle on every button",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Observe one complete press/release cycle from every panel button."""
    args = _parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    try:
        from gpiozero import Button
    except ImportError as error:
        raise SystemExit("GPIO support requires Debian package python3-gpiozero") from error

    finished = Event()
    callback_lock = Lock()
    pressed_at: dict[int, float] = {}
    completed: set[int] = set()
    buttons: dict[int, DiagnosticButton] = {}

    def make_pressed(spec: ButtonSpec) -> Callable[[], None]:
        def pressed() -> None:
            with callback_lock:
                # One physical hold owns one timestamp; duplicate callbacks are
                # ignored until its matching release arrives.
                if spec.gpio in pressed_at:
                    return
                pressed_at[spec.gpio] = time.monotonic()
                print(f"PRESSED name={spec.name} gpio={spec.gpio} level=LOW")

        return pressed

    def make_released(spec: ButtonSpec) -> Callable[[], None]:
        def released() -> None:
            with callback_lock:
                started_at = pressed_at.pop(spec.gpio, None)
                if started_at is None:
                    print(f"UNEXPECTED_RELEASE name={spec.name} gpio={spec.gpio}")
                    return
                duration = time.monotonic() - started_at
                completed.add(spec.gpio)
                print(
                    f"RELEASED name={spec.name} gpio={spec.gpio} level=HIGH "
                    f"duration={duration:.3f}s completed={len(completed)}/{len(BUTTONS)}"
                )
                if len(completed) == len(BUTTONS):
                    finished.set()

        return released

    try:
        for spec in BUTTONS:
            button = Button(
                pin=spec.gpio,
                pull_up=True,
                bounce_time=DEFAULT_CONFIG.buttons.debounce_seconds,
            )
            button.when_pressed = make_pressed(spec)
            button.when_released = make_released(spec)
            buttons[spec.gpio] = button
            print(
                f"READY name={spec.name} gpio={spec.gpio} pressed={button.is_pressed} "
                f"level={active_low_level(is_active=button.is_pressed)}"
            )

        print(
            f"PRESS_EACH_ONCE debounce={DEFAULT_CONFIG.buttons.debounce_seconds:.3f}s "
            f"timeout={args.timeout:g}s"
        )
        if not finished.wait(args.timeout):
            missing = [spec.name for spec in BUTTONS if spec.gpio not in completed]
            print(f"TIMEOUT missing={','.join(missing)}")
            return 2
        print("PASS all panel buttons completed one press/release cycle")
        return 0
    finally:
        # gpiozero owns background callbacks; closing every object guarantees
        # GPIO resources are released even after timeout or Ctrl+C.
        for button in buttons.values():
            button.close()


if __name__ == "__main__":
    raise SystemExit(main())
