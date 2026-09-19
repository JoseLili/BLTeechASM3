"""Small injectable subprocess boundary shared by ALSA diagnostics."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner(Protocol):
    def __call__(
        self,
        arguments: tuple[str, ...],
        *,
        timeout_seconds: float = 10.0,
    ) -> CommandResult: ...


def run_command(
    arguments: tuple[str, ...],
    *,
    timeout_seconds: float = 10.0,
) -> CommandResult:
    """Run one bounded command without a shell or inherited terminal streams."""
    try:
        result = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return CommandResult(returncode=127, stderr=str(error))
    return CommandResult(result.returncode, result.stdout, result.stderr)
