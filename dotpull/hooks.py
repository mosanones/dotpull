"""Pre/post sync hook execution for dotpull profiles."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class HookError(Exception):
    """Raised when a hook fails or is misconfigured."""


@dataclass
class HookResult:
    hook: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run_hook(command: str, cwd: Optional[Path] = None, timeout: int = 30) -> HookResult:
    """Run a single shell hook command and return its result."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        return HookResult(
            hook=command,
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
    except subprocess.TimeoutExpired:
        raise HookError(f"Hook timed out after {timeout}s: {command}")
    except Exception as exc:
        raise HookError(f"Hook execution failed: {exc}") from exc


def run_hooks(
    commands: List[str],
    cwd: Optional[Path] = None,
    timeout: int = 30,
    stop_on_failure: bool = True,
) -> List[HookResult]:
    """Run a list of hook commands sequentially."""
    results: List[HookResult] = []
    for cmd in commands:
        result = run_hook(cmd, cwd=cwd, timeout=timeout)
        results.append(result)
        if stop_on_failure and not result.success:
            raise HookError(
                f"Hook failed (exit {result.returncode}): {cmd}\n{result.stderr}"
            )
    return results


def collect_hooks(profile_data: dict, stage: str) -> List[str]:
    """Extract hook commands for a given stage ('pre_sync' or 'post_sync')."""
    hooks = profile_data.get("hooks", {})
    if not isinstance(hooks, dict):
        raise HookError("'hooks' must be a mapping in the profile configuration.")
    return list(hooks.get(stage, []))
