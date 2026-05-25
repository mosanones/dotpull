"""Rename dotfiles tracked by a profile, updating source paths in-place."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


@dataclass
class RenameResult:
    old_path: str
    new_path: str
    success: bool
    message: str = ""


@dataclass
class RenameSummary:
    results: List[RenameResult] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def summary(self) -> str:
        ok = sum(1 for r in self.results if r.success)
        fail = len(self.results) - ok
        return f"{ok} renamed, {fail} failed"


def rename_dotfile(
    dotfiles_dir: Path,
    old_rel: str,
    new_rel: str,
    *,
    dry_run: bool = False,
) -> RenameResult:
    """Rename a single dotfile within the dotfiles directory.

    Both *old_rel* and *new_rel* are relative to *dotfiles_dir*.
    """
    src = dotfiles_dir / old_rel
    dst = dotfiles_dir / new_rel

    if not src.exists():
        return RenameResult(old_rel, new_rel, False, f"source not found: {src}")

    if dst.exists():
        return RenameResult(old_rel, new_rel, False, f"destination already exists: {dst}")

    if dry_run:
        return RenameResult(old_rel, new_rel, True, "dry-run: no changes made")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return RenameResult(old_rel, new_rel, True, f"renamed {old_rel} -> {new_rel}")


def rename_dotfiles(
    dotfiles_dir: Path,
    pairs: List[tuple[str, str]],
    *,
    dry_run: bool = False,
) -> RenameSummary:
    """Rename multiple dotfiles, returning a summary of all operations."""
    summary = RenameSummary()
    for old_rel, new_rel in pairs:
        result = rename_dotfile(dotfiles_dir, old_rel, new_rel, dry_run=dry_run)
        summary.results.append(result)
    return summary
