"""Symlink management for dotpull — create, remove, and audit dotfile symlinks."""

import os
from pathlib import Path
from typing import Optional


class LinkError(Exception):
    """Raised when a symlink operation fails."""


def create_link(source: Path, target: Path, force: bool = False) -> None:
    """Create a symlink at `target` pointing to `source`.

    Args:
        source: The dotfile inside the dotfiles repository.
        target: The destination path in the user's home directory.
        force: If True, overwrite an existing file/link at `target`.

    Raises:
        LinkError: If the source does not exist or the target cannot be created.
    """
    if not source.exists():
        raise LinkError(f"Source does not exist: {source}")

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() or target.is_symlink():
        if not force:
            raise LinkError(
                f"Target already exists: {target}. Use force=True to overwrite."
            )
        target.unlink()

    target.symlink_to(source.resolve())


def remove_link(target: Path) -> bool:
    """Remove a symlink at `target` if it exists and is a symlink.

    Returns True if the link was removed, False if nothing was done.
    """
    if target.is_symlink():
        target.unlink()
        return True
    return False


def audit_link(source: Path, target: Path) -> str:
    """Return a status string describing the state of a symlink.

    Possible statuses:
        'ok'        — symlink exists and points to the correct source
        'wrong'     — symlink exists but points elsewhere
        'missing'   — target does not exist
        'conflict'  — target exists but is not a symlink
    """
    if not target.exists() and not target.is_symlink():
        return "missing"
    if not target.is_symlink():
        return "conflict"
    if target.resolve() == source.resolve():
        return "ok"
    return "wrong"


def list_managed_links(home_dir: Optional[Path] = None) -> list[tuple[Path, Path]]:
    """Walk `home_dir` and return all symlinks that exist.

    Returns a list of (link_path, resolved_target) tuples.
    """
    if home_dir is None:
        home_dir = Path.home()

    links = []
    for root, _dirs, files in os.walk(home_dir):
        root_path = Path(root)
        for name in files:
            candidate = root_path / name
            if candidate.is_symlink():
                links.append((candidate, candidate.resolve()))
    return links
