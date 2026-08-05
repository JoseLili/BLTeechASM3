"""Observe one debounced panel-button press without dispatching domain events."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from threading import Event, Lock

from asm.config import DEFAULT_CONFIG
from asm.infrastructure.gpio.levels import active_low_level


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpio", type=int, default=17, help="BCM GPIO number (default: 17)")
    parser.add_argument("--name", default="Simulacro", help="human-readable button name")
    parser.add_argument("--timeout", type=float, default=30.0, help="maximum wait in seconds")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Wait for one complete press/release cycle and report its duration."""
    args = _parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    try:
        from gpiozero import Button
    except ImportError as error:
        raise SystemExit("GPIO support requires Debian package python3-gpiozero") from error

    completed = Event()
    callback_lock = Lock()
    pressed_at: float | None = None

    button = Button(
        pin=args.gpio,
        pull_up=True,
        bounce_time=DEFAULT_CONFIG.buttons.debounce_seconds,
    )

    def pressed() -> None:
        nonlocal pressed_at
        with callback_lock:
            # Ignore an unexpected duplicate press until a release completes
            # the current physical gesture.
            if pressed_at is not None:
                return
            pressed_at = time.monotonic()
            print(
                f"PRESSED name={args.name} gpio={args.gpio} "
                f"level={active_low_level(is_active=True)}"
            )

    def released() -> None:
        nonlocal pressed_at
        with callback_lock:
            if pressed_at is None:
                return
            duration = time.monotonic() - pressed_at
            pressed_at = None
            print(
                f"RELEASED name={args.name} gpio={args.gpio} "
                f"level={active_low_level(is_active=False)} duration={duration:.3f}s"
            )
            completed.set()

    button.when_pressed = pressed
    button.when_released = released

    initial_pressed = button.is_pressed
    print(
        f"READY name={args.name} gpio={args.gpio} pressed={initial_pressed} "
        f"level={active_low_level(is_active=initial_pressed)} "
        f"debounce={DEFAULT_CONFIG.buttons.debounce_seconds:.3f}s"
    )
    try:
        if not completed.wait(args.timeout):
            print(f"TIMEOUT no complete press detected within {args.timeout:g}s")
            return 2
        return 0
    finally:
        button.close()


if __name__ == "__main__":
    raise SystemExit(main())
