"""Explicit failures at the ALSA process boundary."""


class AudioUnavailableError(RuntimeError):
    """Raised when card, direction, or codec preload is unavailable."""


class AudioBusyError(RuntimeError):
    """Raised when a second asset would replace one without a policy decision."""


class AudioProcessError(RuntimeError):
    """Raised when an ALSA command cannot start or complete correctly."""
