"""Group management: assign profiles to named groups for bulk operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class GroupError(Exception):
    """Raised when a group operation fails."""


@dataclass
class GroupStore:
    _path: Path
    _data: Dict[str, List[str]] = field(default_factory=dict)

    def load(self) -> "GroupStore":
        if self._path.exists():
            raw = yaml.safe_load(self._path.read_text()) or {}
            if not isinstance(raw, dict):
                raise GroupError(f"Invalid group file: {self._path}")
            self._data = {k: list(v) for k, v in raw.items()}
        return self

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(yaml.dump(self._data, default_flow_style=False))

    def members(self, group: str) -> List[str]:
        return list(self._data.get(group, []))

    def all_groups(self) -> List[str]:
        return list(self._data.keys())

    def add(self, group: str, profile: str) -> None:
        if not group:
            raise GroupError("Group name must not be empty.")
        if not profile:
            raise GroupError("Profile name must not be empty.")
        members = self._data.setdefault(group, [])
        if profile not in members:
            members.append(profile)

    def remove(self, group: str, profile: str) -> bool:
        members = self._data.get(group, [])
        if profile in members:
            members.remove(profile)
            if not members:
                del self._data[group]
            return True
        return False

    def delete_group(self, group: str) -> bool:
        if group in self._data:
            del self._data[group]
            return True
        return False

    def groups_for_profile(self, profile: str) -> List[str]:
        return [g for g, members in self._data.items() if profile in members]


def _store_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".dotpull" / "groups.yaml"


def load_groups(dotfiles_dir: Path) -> GroupStore:
    store = GroupStore(_path=_store_path(dotfiles_dir))
    return store.load()
