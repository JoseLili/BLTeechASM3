"""Minimal physical smoke test for the carrier's 128x64 SSD1306 OLED."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence


def _positive_seconds(value: str) -> float:
    seconds = float(value)
    if seconds <= 0:
        raise argparse.ArgumentTypeError("seconds must be greater than zero")
    return seconds


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bus", type=int, default=1, help="I2C bus number (default: 1)")
    parser.add_argument(
        "--address",
        type=lambda value: int(value, 0),
        default=0x3C,
        help="I2C address in decimal or 0x notation (default: 0x3C)",
    )
    parser.add_argument(
        "--seconds",
        type=_positive_seconds,
        default=10.0,
        help="seconds to keep the test image visible (default: 10)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Draw one image, hold it for inspection, and clear the display."""
    args = _parser().parse_args(argv)

    try:
        from luma.core.interface.serial import i2c
        from luma.core.render import canvas
        from luma.oled.device import ssd1306
    except ImportError as error:
        raise SystemExit(
            "OLED support is unavailable. Install Debian package python3-luma.oled."
        ) from error

    serial = i2c(port=args.bus, address=args.address)
    device = ssd1306(serial, width=128, height=64)

    print(
        f"Showing OLED test on /dev/i2c-{args.bus} at {args.address:#04x} "
        f"for {args.seconds:g} seconds"
    )
    try:
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((25, 7), "ASM BLTeech", fill="white")
            draw.line((8, 23, 119, 23), fill="white")
            draw.text((30, 30), "Prueba OLED", fill="white")
            draw.text((22, 46), "128x64 @ 0x3C", fill="white")
        time.sleep(args.seconds)
    finally:
        device.clear()

    print("OLED test completed and display cleared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
