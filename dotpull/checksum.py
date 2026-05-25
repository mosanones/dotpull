"""Checksum utilities for verifying file integrity across syncs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ChecksumError(Exception):
    """Raised when a checksum operation fails."""


@dataclass
class ChecksumEntry:
    path: str
    sha256: str

    def to_dict(self) -> dict:
        return {"path": self.path, "sha256": self.sha256}

    @staticmethod
    def from_dict(data: dict) -> "ChecksumEntry":
        return ChecksumEntry(path=data["path"], sha256=data["sha256"])


@dataclass
class ChecksumReport:
    entries: List[ChecksumEntry] = field(default_factory=list)
    mismatches: List[str] = field(default_factory=list)

    def healthy(self) -> bool:
        return len(self.mismatches) == 0

    def summary(self) -> str:
        if self.healthy():
            return f"All {len(self.entries)} file(s) verified OK."
        return f"{len(self.mismatches)} mismatch(es) found out of {len(self.entries)} file(s)."


def _file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _store_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".dotpull" / "checksums.json"


def compute_checksums(dotfiles_dir: Path, files: List[str]) -> List[ChecksumEntry]:
    entries = []
    for rel in files:
        src = dotfiles_dir / rel
        if not src.is_file():
            raise ChecksumError(f"Source file not found: {src}")
        entries.append(ChecksumEntry(path=rel, sha256=_file_checksum(src)))
    return entries


def save_checksums(dotfiles_dir: Path, entries: List[ChecksumEntry]) -> None:
    store = _store_path(dotfiles_dir)
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_text(json.dumps([e.to_dict() for e in entries], indent=2))


def load_checksums(dotfiles_dir: Path) -> Dict[str, str]:
    store = _store_path(dotfiles_dir)
    if not store.exists():
        return {}
    data = json.loads(store.read_text())
    return {item["path"]: item["sha256"] for item in data}


def verify_checksums(dotfiles_dir: Path, files: List[str]) -> ChecksumReport:
    stored = load_checksums(dotfiles_dir)
    entries = []
    mismatches = []
    for rel in files:
        src = dotfiles_dir / rel
        if not src.is_file():
            mismatches.append(rel)
            continue
        current = _file_checksum(src)
        entry = ChecksumEntry(path=rel, sha256=current)
        entries.append(entry)
        expected = stored.get(rel)
        if expected is None or expected != current:
            mismatches.append(rel)
    return ChecksumReport(entries=entries, mismatches=mismatches)
