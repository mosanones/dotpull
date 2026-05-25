"""Environment inspection and variable injection for dotpull profiles."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class EnvError(Exception):
    """Raised when an environment operation fails."""


@dataclass
class EnvSnapshot:
    """A filtered snapshot of environment variables relevant to dotpull."""

    variables: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.variables.get(key, default)

    def as_dict(self) -> Dict[str, str]:
        return dict(self.variables)


def capture_env(prefixes: Optional[List[str]] = None) -> EnvSnapshot:
    """Capture current environment variables, optionally filtered by prefix.

    Args:
        prefixes: If given, only include variables whose names start with one
                  of these strings (case-sensitive).  Pass ``None`` to capture
                  everything.

    Returns:
        An :class:`EnvSnapshot` containing the matched variables.
    """
    env = os.environ
    if prefixes is None:
        return EnvSnapshot(variables=dict(env))

    filtered: Dict[str, str] = {
        k: v for k, v in env.items() if any(k.startswith(p) for p in prefixes)
    }
    return EnvSnapshot(variables=filtered)


def inject_env_into_vars(
    base_vars: Dict[str, str],
    snapshot: EnvSnapshot,
    overwrite: bool = True,
) -> Dict[str, str]:
    """Merge *snapshot* variables into *base_vars*.

    Args:
        base_vars:  Existing variable mapping (e.g. from a profile).
        snapshot:   Environment snapshot to merge in.
        overwrite:  When ``True`` (default) env values win over *base_vars*.

    Returns:
        A new dict with the merged result.
    """
    merged = dict(base_vars)
    for k, v in snapshot.variables.items():
        if overwrite or k not in merged:
            merged[k] = v
    return merged


def required_env(keys: List[str]) -> Dict[str, str]:
    """Return a dict of the requested env keys, raising if any are missing.

    Raises:
        EnvError: if one or more keys are absent from the environment.
    """
    missing = [k for k in keys if k not in os.environ]
    if missing:
        raise EnvError(f"Required environment variable(s) not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in keys}
