"""Tests for dotpull.clean."""
from __future__ import annotations

from pathlib import Path

import pytest

from dotpull.clean import clean_broken_symlinks, clean_stale_links


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeProfile:
    def __init__(self, files: dict):
        self.files = files
        self.variables = {}
        self.extends = None


# ---------------------------------------------------------------------------
# clean_stale_links
# ---------------------------------------------------------------------------

def test_clean_stale_links_removes_dead_source(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()

    # source does NOT exist
    target = home / ".bashrc"
    source = dotfiles / ".bashrc"
    target.symlink_to(source)  # broken symlink

    profile = _FakeProfile({".bashrc": ".bashrc"})
    result = clean_stale_links(profile, home, dotfiles, dry_run=False)

    assert ".bashrc" in result.summary() or "removed 1" in result.summary()
    assert str(target) in result.removed
    assert not target.exists()


def test_clean_stale_links_dry_run_does_not_delete(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()

    target = home / ".vimrc"
    source = dotfiles / ".vimrc"
    target.symlink_to(source)

    profile = _FakeProfile({".vimrc": ".vimrc"})
    result = clean_stale_links(profile, home, dotfiles, dry_run=True)

    assert str(target) in result.removed
    assert target.is_symlink()  # still exists
    assert result.dry_run is True


def test_clean_stale_links_skips_valid_link(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()

    source = dotfiles / ".tmux.conf"
    source.write_text("set -g mouse on")
    target = home / ".tmux.conf"
    target.symlink_to(source)

    profile = _FakeProfile({".tmux.conf": ".tmux.conf"})
    result = clean_stale_links(profile, home, dotfiles, dry_run=False)

    assert result.removed == []
    assert target.is_symlink()  # untouched


# ---------------------------------------------------------------------------
# clean_broken_symlinks
# ---------------------------------------------------------------------------

def test_clean_broken_symlinks_removes_dead_links(tmp_path):
    dead = tmp_path / "dead_link"
    dead.symlink_to(tmp_path / "nonexistent")

    result = clean_broken_symlinks(tmp_path, dry_run=False)

    assert str(dead) in result.removed
    assert not dead.exists()


def test_clean_broken_symlinks_dry_run(tmp_path):
    dead = tmp_path / "dead2"
    dead.symlink_to(tmp_path / "ghost")

    result = clean_broken_symlinks(tmp_path, dry_run=True)

    assert str(dead) in result.removed
    assert dead.is_symlink()  # untouched


def test_clean_broken_symlinks_missing_dir_returns_empty():
    result = clean_broken_symlinks(Path("/nonexistent/path/xyz"))
    assert result.removed == []
    assert result.healthy()
