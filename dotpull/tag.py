"""Tag management for dotfile profiles — assign, remove, and filter profiles by tag."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class TagError(Exception):
    """Raised when a tag operation fails."""


@dataclass
class TagStore:
    path: Path
    _data: Dict[str, List[str]] = field(default_factory=dict)

    def load(self) -> None:
        if self.path.exists():
            raw = yaml.safe_load(self.path.read_text()) or {}
            self._data = {k: list(v) for k, v in raw.items()}
        else:
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.dump(self._data, default_flow_style=False))

    def tags_for(self, profile: str) -> List[str]:
        return list(self._data.get(profile, []))

    def profiles_for(self, tag: str) -> List[str]:
        return [p for p, tags in self._data.items() if tag in tags]

    def add_tag(self, profile: str, tag: str) -> None:
        tags = self._data.setdefault(profile, [])
        if tag not in tags:
            tags.append(tag)

    def remove_tag(self, profile: str, tag: str) -> None:
        tags = self._data.get(profile, [])
        if tag not in tags:
            raise TagError(f"Profile '{profile}' does not have tag '{tag}'")
        tags.remove(tag)
        if not tags:
            del self._data[profile]

    def all_tags(self) -> List[str]:
        seen: List[str] = []
        for tags in self._data.values():
            for t in tags:
                if t not in seen:
                    seen.append(t)
        return seen


def _store_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".dotpull" / "tags.yaml"


def load_tag_store(dotfiles_dir: Path) -> TagStore:
    store = TagStore(path=_store_path(dotfiles_dir))
    store.load()
    return store
