"""prune.py — Remove orphaned symlinks and stale snapshot entries."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotpull.snapshot import _snapshot_dir, list_snapshots


@dataclass
class PruneResult:
    removed_links: List[str] = field(default_factory=list)
    removed_snapshots: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        parts = []
        if self.removed_links:
            parts.append(f"{len(self.removed_links)} orphaned link(s) removed")
        if self.removed_snapshots:
            parts.append(f"{len(self.removed_snapshots)} stale snapshot(s) removed")
        if not parts:
            return "Nothing to prune."
        return "; ".join(parts) + "."


def prune_orphaned_links(home_dir: Path, dry_run: bool = False) -> PruneResult:
    """Walk home_dir recursively and remove symlinks whose targets do not exist."""
    result = PruneResult()
    for root, _dirs, files in os.walk(home_dir):
        for name in files:
            full = Path(root) / name
            if full.is_symlink() and not full.exists():
                result.removed_links.append(str(full))
                if not dry_run:
                    try:
                        full.unlink()
                    except OSError as exc:
                        result.errors.append(f"Cannot remove {full}: {exc}")
    return result


def prune_old_snapshots(
    dotfiles_dir: Path,
    keep: int = 5,
    dry_run: bool = False,
) -> PruneResult:
    """Keep only the *keep* most-recent snapshots; remove the rest."""
    result = PruneResult()
    if keep < 1:
        result.errors.append("keep must be >= 1")
        return result

    snapshots = list_snapshots(dotfiles_dir)
    # list_snapshots returns newest-first by convention (sorted by name desc)
    snapshots_sorted = sorted(snapshots, reverse=True)
    to_remove = snapshots_sorted[keep:]

    snap_base = _snapshot_dir(dotfiles_dir)
    for name in to_remove:
        snap_path = snap_base / name
        result.removed_snapshots.append(name)
        if not dry_run:
            try:
                import shutil
                shutil.rmtree(snap_path)
            except OSError as exc:
                result.errors.append(f"Cannot remove snapshot {name}: {exc}")

    return result
