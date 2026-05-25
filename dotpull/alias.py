"""Profile alias management — create short names that point to profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class AliasError(Exception):
    """Raised when an alias operation fails."""


@dataclass
class AliasStore:
    _data: Dict[str, str] = field(default_factory=dict)
    _path: Optional[Path] = field(default=None, repr=False)

    # ------------------------------------------------------------------
    def get(self, name: str) -> Optional[str]:
        """Return the profile name for *name*, or None if not found."""
        return self._data.get(name)

    def set(self, name: str, profile: str) -> None:
        """Create or overwrite an alias."""
        if not name or not profile:
            raise AliasError("Alias name and target profile must be non-empty.")
        self._data[name] = profile

    def remove(self, name: str) -> bool:
        """Remove *name*. Returns True if it existed."""
        if name in self._data:
            del self._data[name]
            return True
        return False

    def all(self) -> Dict[str, str]:
        """Return a shallow copy of all aliases."""
        return dict(self._data)

    def save(self) -> None:
        if self._path is None:
            raise AliasError("No path configured for AliasStore.")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            yaml.safe_dump(self._data, fh)


def _alias_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".dotpull" / "aliases.yaml"


def load(dotfiles_dir: Path) -> AliasStore:
    """Load aliases from *dotfiles_dir*; returns empty store if absent."""
    path = _alias_path(dotfiles_dir)
    store = AliasStore(_path=path)
    if not path.exists():
        return store
    try:
        raw = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise AliasError(f"Failed to parse aliases file: {exc}") from exc
    if not isinstance(raw, dict):
        raise AliasError("aliases.yaml must contain a mapping.")
    store._data = {str(k): str(v) for k, v in raw.items()}
    return store


def resolve_alias(store: AliasStore, name: str) -> str:
    """Return the profile that *name* points to, or *name* itself."""
    return store.get(name) or name
