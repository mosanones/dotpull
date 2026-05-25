"""Tests for dotpull.prune."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from dotpull.prune import prune_old_snapshots, prune_orphaned_links


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def home_dir(tmp_path: Path) -> Path:
    d = tmp_path / "home"
    d.mkdir()
    return d


@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    (d / ".snapshots").mkdir(parents=True)
    return d


# ---------------------------------------------------------------------------
# prune_orphaned_links
# ---------------------------------------------------------------------------

def test_prune_removes_dead_symlink(home_dir: Path) -> None:
    dead_target = home_dir / "ghost"
    link = home_dir / ".bashrc"
    link.symlink_to(dead_target)  # target does not exist

    result = prune_orphaned_links(home_dir)

    assert str(link) in result.removed_links
    assert not link.exists()
    assert link.is_symlink() is False


def test_prune_leaves_valid_symlink(home_dir: Path) -> None:
    real_file = home_dir / "real.txt"
    real_file.write_text("hi")
    link = home_dir / ".vimrc"
    link.symlink_to(real_file)

    result = prune_orphaned_links(home_dir)

    assert str(link) not in result.removed_links
    assert link.is_symlink()


def test_prune_dry_run_does_not_delete(home_dir: Path) -> None:
    link = home_dir / ".zshrc"
    link.symlink_to(home_dir / "nowhere")

    result = prune_orphaned_links(home_dir, dry_run=True)

    assert str(link) in result.removed_links
    assert link.is_symlink()  # still there


# ---------------------------------------------------------------------------
# prune_old_snapshots
# ---------------------------------------------------------------------------

def _make_snapshots(dotfiles_dir: Path, names: list) -> None:
    base = dotfiles_dir / ".snapshots"
    for name in names:
        (base / name).mkdir()


def test_prune_snapshots_keeps_newest(dotfiles_dir: Path) -> None:
    snaps = ["2024-01-01_a", "2024-01-02_b", "2024-01-03_c", "2024-01-04_d"]
    _make_snapshots(dotfiles_dir, snaps)

    result = prune_old_snapshots(dotfiles_dir, keep=2)

    assert len(result.removed_snapshots) == 2
    remaining = list((dotfiles_dir / ".snapshots").iterdir())
    assert len(remaining) == 2
    assert all(r.name in ["2024-01-04_d", "2024-01-03_c"] for r in remaining)


def test_prune_snapshots_dry_run_keeps_all(dotfiles_dir: Path) -> None:
    snaps = ["2024-01-01_a", "2024-01-02_b", "2024-01-03_c"]
    _make_snapshots(dotfiles_dir, snaps)

    result = prune_old_snapshots(dotfiles_dir, keep=1, dry_run=True)

    assert len(result.removed_snapshots) == 2
    remaining = list((dotfiles_dir / ".snapshots").iterdir())
    assert len(remaining) == 3  # nothing actually deleted


def test_prune_snapshots_invalid_keep_returns_error(dotfiles_dir: Path) -> None:
    result = prune_old_snapshots(dotfiles_dir, keep=0)
    assert not result.healthy
    assert "keep must be >= 1" in result.errors[0]
