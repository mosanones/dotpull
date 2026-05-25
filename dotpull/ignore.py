"""Manage per-profile ignore patterns for dotpull."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml

IGNORE_FILENAME = ".dotpullignore"


class IgnoreError(Exception):
    """Raised when ignore store operations fail."""


@dataclass
class IgnoreStore:
    dotfiles_dir: Path
    _patterns: dict[str, List[str]] = field(default_factory=dict)

    def _path(self) -> Path:
        return self.dotfiles_dir / IGNORE_FILENAME

    def load(self) -> "IgnoreStore":
        p = self._path()
        if not p.exists():
            self._patterns = {}
            return self
        try:
            data = yaml.safe_load(p.read_text()) or {}
        except yaml.YAMLError as exc:
            raise IgnoreError(f"Failed to parse {p}: {exc}") from exc
        if not isinstance(data, dict):
            raise IgnoreError(f"{p} must contain a YAML mapping")
        self._patterns = {k: list(v) for k, v in data.items()}
        return self

    def save(self) -> None:
        self._path().write_text(yaml.safe_dump(self._patterns, default_flow_style=False))

    def patterns_for(self, profile: str) -> List[str]:
        global_pats = self._patterns.get("*", [])
        profile_pats = self._patterns.get(profile, [])
        return global_pats + profile_pats

    def add(self, profile: str, pattern: str) -> None:
        self._patterns.setdefault(profile, [])
        if pattern not in self._patterns[profile]:
            self._patterns[profile].append(pattern)

    def remove(self, profile: str, pattern: str) -> bool:
        pats = self._patterns.get(profile, [])
        if pattern in pats:
            pats.remove(pattern)
            self._patterns[profile] = pats
            return True
        return False

    def list_all(self) -> dict[str, List[str]]:
        return dict(self._patterns)


def is_ignored(path: str, patterns: List[str]) -> bool:
    """Return True if *path* matches any of the given glob patterns."""
    name = Path(path).name
    for pat in patterns:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(path, pat):
            return True
    return False
