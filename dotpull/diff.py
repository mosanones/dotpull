"""Diff utilities for comparing dotfiles against their symlink targets."""

from __future__ import annotations

import difflib
import os
from pathlib import Path
from typing import NamedTuple


class DiffResult(NamedTuple):
    source: Path
    target: Path
    status: str  # 'same', 'differs', 'missing_target', 'missing_source', 'not_a_link'
    unified_diff: list[str]


def diff_file(source: Path, target: Path) -> DiffResult:
    """Compare a dotfile source against its deployed target."""
    if not source.exists():
        return DiffResult(source, target, "missing_source", [])

    if not target.exists():
        return DiffResult(source, target, "missing_target", [])

    if target.is_symlink():
        resolved = target.resolve()
        if resolved == source.resolve():
            return DiffResult(source, target, "same", [])

    try:
        source_lines = source.read_text(errors="replace").splitlines(keepends=True)
        target_lines = target.read_text(errors="replace").splitlines(keepends=True)
    except OSError:
        return DiffResult(source, target, "differs", [])

    if source_lines == target_lines:
        return DiffResult(source, target, "same", [])

    diff = list(
        difflib.unified_diff(
            target_lines,
            source_lines,
            fromfile=str(target),
            tofile=str(source),
        )
    )
    return DiffResult(source, target, "differs", diff)


def diff_profile_files(
    dotfiles_dir: Path,
    file_map: dict[str, str],
    home_dir: Path | None = None,
) -> list[DiffResult]:
    """Diff all files in a profile's file map.

    Args:
        dotfiles_dir: Root directory of dotfiles repo.
        file_map: Mapping of repo-relative source path -> absolute or home-relative target.
        home_dir: Override for home directory (defaults to Path.home()).

    Returns:
        List of DiffResult for each file.
    """
    if home_dir is None:
        home_dir = Path.home()

    results: list[DiffResult] = []
    for rel_src, raw_target in file_map.items():
        source = dotfiles_dir / rel_src
        target_path = Path(raw_target)
        if not target_path.is_absolute():
            target_path = home_dir / target_path
        results.append(diff_file(source, target_path))
    return results
