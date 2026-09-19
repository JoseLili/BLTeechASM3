"""Apply and verify the validated GOLD receive profile on the real SA818S-V."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from asm.application.receiver_service import ReceiverService
from asm.config import DEFAULT_CONFIG
from asm.domain.receiver import ReceiverChannel, ReceiverProfile
from asm.infrastructure.receiver.sa818_serial import Sa818Error, Sa818SerialReceiver


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--channel",
        choices=[channel.value for channel in ReceiverChannel],
        default=DEFAULT_CONFIG.receiver.channel.value,
    )
    parser.add_argument("--device", default=DEFAULT_CONFIG.receiver.serial_device)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Configure one receive channel and print the verified protocol evidence."""
    args = _parser().parse_args(argv)
    profile = ReceiverProfile.gold(ReceiverChannel(args.channel))
    receiver = Sa818SerialReceiver.open(
        device=args.device,
        timeout_seconds=DEFAULT_CONFIG.receiver.command_timeout_seconds,
        settle_seconds=DEFAULT_CONFIG.receiver.startup_settle_seconds,
    )
    try:
        result = ReceiverService(receiver).configure(profile)
    except Sa818Error as error:
        print(f"FAIL {error}")
        return 2
    finally:
        receiver.close()

    for response in result.responses:
        print(response)
    print(
        f"PASS {result.model} {result.profile.channel.value} "
        f"{result.profile.channel.frequency_text} MHz RX-only verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
