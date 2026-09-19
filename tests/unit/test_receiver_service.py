from __future__ import annotations

from dataclasses import dataclass

import pytest

from asm.application.receiver_service import ReceiverService, ReceiverVerificationError
from asm.domain.receiver import (
    ReceiverChannel,
    ReceiverConfigurationResult,
    ReceiverProfile,
)


@dataclass
class FakeReceiver:
    result: ReceiverConfigurationResult
    requested: ReceiverProfile | None = None

    def configure(self, profile: ReceiverProfile) -> ReceiverConfigurationResult:
        self.requested = profile
        return self.result


def test_service_returns_matching_verified_configuration() -> None:
    profile = ReceiverProfile.gold()
    result = ReceiverConfigurationResult("fake", profile, ("ok",), True)
    receiver = FakeReceiver(result)

    assert ReceiverService(receiver).configure(profile) is result
    assert receiver.requested is profile


@pytest.mark.parametrize("verified", [False, True])
def test_service_rejects_unverified_or_different_result(verified: bool) -> None:
    requested = ReceiverProfile.gold(ReceiverChannel.C7)
    returned = requested if not verified else ReceiverProfile.gold(ReceiverChannel.C6)
    receiver = FakeReceiver(ReceiverConfigurationResult("fake", returned, (), verified))

    with pytest.raises(ReceiverVerificationError):
        ReceiverService(receiver).configure(requested)

