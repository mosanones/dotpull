"""Clean stale/orphaned entries from dotpull tracking files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotpull.profile import Profile


@dataclass
class CleanResult:
    removed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    dry_run: bool = False

    def healthy(self) -> bool:
        return len(self.removed) == 0 and len(self.skipped) == 0

    def summary(self) -> str:
        if self.dry_run:
            prefix = "[dry-run] "
        else:
            prefix = ""
        parts = []
        if self.removed:
            parts.append(f"{prefix}removed {len(self.removed)} stale link(s)")
        if self.skipped:
            parts.append(f"{prefix}skipped {len(self.skipped)} item(s)")
        if not parts:
            return f"{prefix}nothing to clean"
        return "; ".join(parts)


def clean_stale_links(
    profile: Profile,
    home_dir: Path,
    dotfiles_dir: Path,
    dry_run: bool = False,
) -> CleanResult:
    """Remove symlinks in home_dir that point into dotfiles_dir but whose
    source file no longer exists."""
    result = CleanResult(dry_run=dry_run)

    managed_sources = {dotfiles_dir / rel for rel in profile.files.values()}

    for target_rel, source_rel in profile.files.items():
        target = home_dir / target_rel
        source = dotfiles_dir / source_rel

        if not target.is_symlink():
            continue

        resolved = target.resolve()
        if resolved != source.resolve() and source not in managed_sources:
            result.skipped.append(str(target))
            continue

        if not source.exists():
            result.removed.append(str(target))
            if not dry_run:
                target.unlink()

    return result


def clean_broken_symlinks(directory: Path, dry_run: bool = False) -> CleanResult:
    """Recursively remove broken symlinks under *directory*."""
    result = CleanResult(dry_run=dry_run)

    if not directory.exists():
        return result

    for path in directory.rglob("*"):
        if path.is_symlink() and not path.exists():
            result.removed.append(str(path))
            if not dry_run:
                path.unlink()

    return result
