"""Archive management: compress and restore dotfile archives."""

from __future__ import annotations

import hashlib
import shutil
import tarfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class ArchiveError(Exception):
    pass


@dataclass
class ArchiveResult:
    path: Path
    label: str
    files: List[str] = field(default_factory=list)
    checksum: str = ""

    @property
    def healthy(self) -> bool:
        return bool(self.checksum)


def _archive_dir(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".archives"


def _file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def create_archive(dotfiles_dir: Path, label: Optional[str] = None) -> ArchiveResult:
    """Create a compressed tar archive of the dotfiles directory."""
    if not dotfiles_dir.exists():
        raise ArchiveError(f"Dotfiles directory not found: {dotfiles_dir}")

    archive_dir = _archive_dir(dotfiles_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    slug = f"{label}-{ts}" if label else ts
    archive_path = archive_dir / f"{slug}.tar.gz"

    collected: List[str] = []
    with tarfile.open(archive_path, "w:gz") as tar:
        for item in sorted(dotfiles_dir.rglob("*")):
            if item.is_file() and archive_dir not in item.parents:
                rel = item.relative_to(dotfiles_dir)
                tar.add(item, arcname=str(rel))
                collected.append(str(rel))

    checksum = _file_checksum(archive_path)
    return ArchiveResult(path=archive_path, label=slug, files=collected, checksum=checksum)


def list_archives(dotfiles_dir: Path) -> List[ArchiveResult]:
    """Return all archives sorted newest-first."""
    archive_dir = _archive_dir(dotfiles_dir)
    if not archive_dir.exists():
        return []
    results = []
    for p in sorted(archive_dir.glob("*.tar.gz"), reverse=True):
        results.append(ArchiveResult(path=p, label=p.stem, checksum=_file_checksum(p)))
    return results


def restore_archive(archive_path: Path, target_dir: Path, overwrite: bool = False) -> List[str]:
    """Extract an archive into target_dir. Returns list of restored paths."""
    if not archive_path.exists():
        raise ArchiveError(f"Archive not found: {archive_path}")
    if not tarfile.is_tarfile(archive_path):
        raise ArchiveError(f"Not a valid tar archive: {archive_path}")

    target_dir.mkdir(parents=True, exist_ok=True)
    restored: List[str] = []
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            dest = target_dir / member.name
            if dest.exists() and not overwrite:
                continue
            tar.extract(member, path=target_dir)
            restored.append(member.name)
    return restored
