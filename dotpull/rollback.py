"""Rollback support: restore a profile's dotfiles from a snapshot."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotpull.snapshot import _snapshot_dir, SnapshotError


@dataclass
class RollbackResult:
    snapshot_label: str
    restored: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def rollback_profile(
    dotfiles_dir: Path,
    profile_name: str,
    label: str,
    dry_run: bool = False,
) -> RollbackResult:
    """Restore dotfiles for *profile_name* from the snapshot identified by *label*."""
    snap_dir = _snapshot_dir(dotfiles_dir) / label
    if not snap_dir.exists():
        raise SnapshotError(f"Snapshot '{label}' not found in {_snapshot_dir(dotfiles_dir)}")

    manifest_path = snap_dir / "manifest.json"
    if not manifest_path.exists():
        raise SnapshotError(f"Snapshot '{label}' is missing a manifest.json")

    manifest = json.loads(manifest_path.read_text())
    result = RollbackResult(snapshot_label=label)

    for entry in manifest.get("files", []):
        rel = entry["path"]
        src = snap_dir / rel
        dst = dotfiles_dir / rel

        if not src.exists():
            result.skipped.append(rel)
            continue

        try:
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            result.restored.append(rel)
        except OSError as exc:
            result.errors.append(f"{rel}: {exc}")

    return result


def list_rollback_targets(dotfiles_dir: Path) -> List[str]:
    """Return snapshot labels available for rollback, newest first."""
    snap_root = _snapshot_dir(dotfiles_dir)
    if not snap_root.exists():
        return []
    labels = sorted(
        (d.name for d in snap_root.iterdir() if d.is_dir()),
        reverse=True,
    )
    return labels
