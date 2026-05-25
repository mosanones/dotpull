"""Watch dotfiles directory for changes and auto-sync on modification."""

import time
import logging
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger(__name__)


class WatchError(Exception):
    pass


def _get_mtimes(dotfiles_dir: Path, profile_files: list[str]) -> dict[str, float]:
    """Return a mapping of filepath -> mtime for all tracked files."""
    mtimes = {}
    for rel in profile_files:
        p = dotfiles_dir / rel
        if p.exists():
            mtimes[str(p)] = p.stat().st_mtime
    return mtimes


def _detect_changes(
    dotfiles_dir: Path,
    profile_files: list[str],
    previous: dict[str, float],
    current: dict[str, float],
) -> list[str]:
    """Return relative paths whose mtime changed, appeared, or disappeared."""
    return [
        rel
        for rel in profile_files
        if current.get(str(dotfiles_dir / rel)) != previous.get(str(dotfiles_dir / rel))
    ]


def watch_profile(
    dotfiles_dir: Path,
    profile_files: list[str],
    on_change: Callable[[list[str]], None],
    interval: float = 1.0,
    stop_after: Optional[int] = None,
) -> None:
    """
    Poll tracked files and invoke `on_change` with a list of changed paths.

    Args:
        dotfiles_dir: Root directory of dotfiles.
        profile_files: Relative paths to watch.
        on_change: Callback receiving list of changed relative paths.
        interval: Polling interval in seconds.
        stop_after: Stop after this many iterations (None = run forever).
    """
    if not dotfiles_dir.is_dir():
        raise WatchError(f"Dotfiles directory not found: {dotfiles_dir}")

    previous = _get_mtimes(dotfiles_dir, profile_files)
    iterations = 0

    log.info("Watching %d file(s) in %s", len(profile_files), dotfiles_dir)

    while stop_after is None or iterations < stop_after:
        time.sleep(interval)
        current = _get_mtimes(dotfiles_dir, profile_files)
        changed = _detect_changes(dotfiles_dir, profile_files, previous, current)
        if changed:
            log.info("Detected changes: %s", changed)
            on_change(changed)
            previous = current
        iterations += 1
