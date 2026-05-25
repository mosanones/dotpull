"""copy.py — Copy a dotfile from the filesystem into the dotfiles repo."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path


class CopyError(Exception):
    """Raised when a copy operation fails."""


@dataclass
class CopyResult:
    source: Path
    destination: Path
    backed_up: Path | None = None
    skipped: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if self.skipped:
            return f"skipped {self.source} (dry-run)"
        if self.backed_up:
            return f"copied {self.source} -> {self.destination} (backup: {self.backed_up})"
        return f"copied {self.source} -> {self.destination}"


def copy_into_repo(
    source: Path,
    dotfiles_dir: Path,
    relative_dest: str | None = None,
    *,
    overwrite: bool = False,
    dry_run: bool = False,
) -> CopyResult:
    """Copy *source* into *dotfiles_dir*, optionally under *relative_dest*.

    If *relative_dest* is None the file is placed at the same relative
    position inside *dotfiles_dir* (mirroring the absolute path stripped
    of its root).
    """
    if not source.exists():
        raise CopyError(f"Source file does not exist: {source}")
    if source.is_dir():
        raise CopyError(f"Source must be a file, not a directory: {source}")

    if relative_dest:
        dest = dotfiles_dir / relative_dest
    else:
        # Strip leading '/' so Path('/home/user/.bashrc') -> 'home/user/.bashrc'
        dest = dotfiles_dir / str(source).lstrip("/")

    backed_up: Path | None = None

    if dry_run:
        return CopyResult(source=source, destination=dest, skipped=True)

    if dest.exists() and not overwrite:
        raise CopyError(
            f"Destination already exists: {dest}. Use overwrite=True to replace."
        )

    if dest.exists() and overwrite:
        backup = dest.with_suffix(dest.suffix + ".bak")
        shutil.copy2(dest, backup)
        backed_up = backup

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return CopyResult(source=source, destination=dest, backed_up=backed_up)
