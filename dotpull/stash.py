"""Stash and restore uncommitted dotfile changes temporarily."""
from __future__ import annotations

import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


class StashError(Exception):
    pass


@dataclass
class StashEntry:
    stash_id: str
    profile: str
    timestamp: float
    files: List[str]
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "stash_id": self.stash_id,
            "profile": self.profile,
            "timestamp": self.timestamp,
            "files": self.files,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StashEntry":
        return cls(
            stash_id=data["stash_id"],
            profile=data["profile"],
            timestamp=data["timestamp"],
            files=data.get("files", []),
            message=data.get("message", ""),
        )


def _stash_dir(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".stash"


def _index_path(dotfiles_dir: Path) -> Path:
    return _stash_dir(dotfiles_dir) / "index.yaml"


def load_index(dotfiles_dir: Path) -> List[StashEntry]:
    path = _index_path(dotfiles_dir)
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text()) or []
    return [StashEntry.from_dict(d) for d in data]


def _save_index(dotfiles_dir: Path, entries: List[StashEntry]) -> None:
    path = _index_path(dotfiles_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump([e.to_dict() for e in entries], default_flow_style=False))


def stash_files(
    dotfiles_dir: Path,
    profile: str,
    file_paths: List[Path],
    message: str = "",
) -> StashEntry:
    """Copy current versions of file_paths into a stash slot."""
    if not file_paths:
        raise StashError("No files provided to stash.")
    stash_id = f"{int(time.time() * 1000)}"
    slot = _stash_dir(dotfiles_dir) / stash_id
    slot.mkdir(parents=True, exist_ok=True)
    stored: List[str] = []
    for fp in file_paths:
        if not fp.exists():
            raise StashError(f"File not found: {fp}")
        dest = slot / fp.name
        shutil.copy2(fp, dest)
        stored.append(str(fp))
    entry = StashEntry(stash_id=stash_id, profile=profile, timestamp=time.time(), files=stored, message=message)
    index = load_index(dotfiles_dir)
    index.append(entry)
    _save_index(dotfiles_dir, index)
    return entry


def pop_stash(dotfiles_dir: Path, stash_id: str, dry_run: bool = False) -> StashEntry:
    """Restore files from a stash slot and remove the entry."""
    index = load_index(dotfiles_dir)
    matches = [e for e in index if e.stash_id == stash_id]
    if not matches:
        raise StashError(f"Stash not found: {stash_id}")
    entry = matches[0]
    slot = _stash_dir(dotfiles_dir) / stash_id
    for fp_str in entry.files:
        src = slot / Path(fp_str).name
        if not src.exists():
            raise StashError(f"Stash slot missing file: {src}")
        if not dry_run:
            dest = Path(fp_str)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    if not dry_run:
        shutil.rmtree(slot, ignore_errors=True)
        _save_index(dotfiles_dir, [e for e in index if e.stash_id != stash_id])
    return entry
