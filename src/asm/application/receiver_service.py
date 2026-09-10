"""Application service for receiver startup and channel changes."""

from __future__ import annotations

from dataclasses import dataclass

from asm.application.ports import ReceiverPort
from asm.domain.receiver import ReceiverConfigurationResult, ReceiverProfile


class ReceiverVerificationError(RuntimeError):
    """Raised when an adapter cannot prove that the requested profile is active."""


@dataclass(slots=True)
class ReceiverService:
    """Apply a profile only when the receiver confirms the same configuration."""

    receiver: ReceiverPort

    def configure(self, profile: ReceiverProfile) -> ReceiverConfigurationResult:
        result = self.receiver.configure(profile)
        if not result.verified or result.profile != profile:
            raise ReceiverVerificationError("receiver did not verify the requested profile")
        return result

