"""Core sync logic: symlink or copy dotfiles to their target locations."""

import shutil
from pathlib import Path
from typing import Callable

from dotpull.profile import Profile


def sync_profile(
    profile: Profile,
    *,
    backup: bool = True,
    backup_dir: Path | None = None,
    dry_run: bool = False,
    symlink: bool = True,
    log: Callable[[str], None] = print,
) -> list[str]:
    """Sync all files in the profile. Returns a list of actions taken."""
    actions = []
    file_map = profile.resolve_files()

    for source, target in file_map.items():
        if not source.exists():
            log(f"[SKIP] Source not found: {source}")
            continue

        if target.exists() or target.is_symlink():
            if backup and backup_dir:
                _backup_file(target, backup_dir, dry_run=dry_run, log=log)
            if not dry_run:
                target.unlink() if target.is_symlink() else target.unlink()

        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            if symlink:
                target.symlink_to(source)
            else:
                shutil.copy2(source, target)

        action = "symlink" if symlink else "copy"
        msg = f"[{action.upper()}] {source} -> {target}"
        if dry_run:
            msg = f"[DRY-RUN] {msg}"
        log(msg)
        actions.append(msg)

    return actions


def _backup_file(
    target: Path,
    backup_dir: Path,
    dry_run: bool = False,
    log: Callable[[str], None] = print,
) -> None:
    """Back up an existing target file before overwriting."""
    relative = target.relative_to(Path.home()) if target.is_relative_to(Path.home()) else target.name
    dest = backup_dir / relative
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
    log(f"[BACKUP] {target} -> {dest}")
