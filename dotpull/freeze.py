"""freeze.py – Capture a point-in-time snapshot of resolved variables for a profile.

A 'freeze' records the fully-resolved variable set (config + parent + profile +
env overrides) so you can compare future states or audit drift.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class FreezeError(Exception):
    """Raised when a freeze operation fails."""


@dataclass
class FreezeEntry:
    profile: str
    timestamp: float
    variables: Dict[str, str]
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "timestamp": self.timestamp,
            "variables": self.variables,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FreezeEntry":
        return cls(
            profile=data["profile"],
            timestamp=data["timestamp"],
            variables=data["variables"],
            label=data.get("label", ""),
        )


def _freeze_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".dotpull" / "freezes.json"


def load_freezes(dotfiles_dir: Path) -> List[FreezeEntry]:
    path = _freeze_path(dotfiles_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise FreezeError(f"Cannot read freeze store: {exc}") from exc
    return [FreezeEntry.from_dict(d) for d in data]


def save_freezes(dotfiles_dir: Path, entries: List[FreezeEntry]) -> None:
    path = _freeze_path(dotfiles_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([e.to_dict() for e in entries], indent=2))


def freeze_profile(
    dotfiles_dir: Path,
    profile: str,
    variables: Dict[str, str],
    label: str = "",
) -> FreezeEntry:
    """Record the current resolved variables for *profile* and persist them."""
    if not profile:
        raise FreezeError("profile name must not be empty")
    entry = FreezeEntry(
        profile=profile,
        timestamp=time.time(),
        variables=dict(variables),
        label=label,
    )
    existing = load_freezes(dotfiles_dir)
    existing.append(entry)
    save_freezes(dotfiles_dir, existing)
    return entry


def list_freezes(dotfiles_dir: Path, profile: Optional[str] = None) -> List[FreezeEntry]:
    """Return all freeze entries, optionally filtered by profile name."""
    entries = load_freezes(dotfiles_dir)
    if profile:
        entries = [e for e in entries if e.profile == profile]
    return entries
