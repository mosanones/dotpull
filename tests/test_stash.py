"""Tests for dotpull.stash."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from dotpull.stash import StashError, load_index, pop_stash, stash_files


@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


@pytest.fixture()
def sample_files(tmp_path: Path) -> list[Path]:
    f1 = tmp_path / "bashrc"
    f1.write_text("export FOO=1")
    f2 = tmp_path / "vimrc"
    f2.write_text("set number")
    return [f1, f2]


def test_stash_files_creates_entry(dotfiles_dir, sample_files):
    entry = stash_files(dotfiles_dir, "default", sample_files, message="wip")
    assert entry.profile == "default"
    assert entry.message == "wip"
    assert len(entry.files) == 2
    assert entry.stash_id


def test_stash_files_persists_index(dotfiles_dir, sample_files):
    stash_files(dotfiles_dir, "default", sample_files)
    index = load_index(dotfiles_dir)
    assert len(index) == 1


def test_stash_multiple_entries(dotfiles_dir, sample_files):
    stash_files(dotfiles_dir, "default", [sample_files[0]])
    time.sleep(0.01)
    stash_files(dotfiles_dir, "work", [sample_files[1]])
    index = load_index(dotfiles_dir)
    assert len(index) == 2
    profiles = {e.profile for e in index}
    assert profiles == {"default", "work"}


def test_stash_missing_file_raises(dotfiles_dir, tmp_path):
    missing = tmp_path / "ghost.txt"
    with pytest.raises(StashError, match="File not found"):
        stash_files(dotfiles_dir, "default", [missing])


def test_stash_empty_files_raises(dotfiles_dir):
    with pytest.raises(StashError, match="No files"):
        stash_files(dotfiles_dir, "default", [])


def test_pop_restores_file_content(dotfiles_dir, sample_files):
    original_content = sample_files[0].read_text()
    entry = stash_files(dotfiles_dir, "default", [sample_files[0]])
    sample_files[0].write_text("modified content")
    pop_stash(dotfiles_dir, entry.stash_id)
    assert sample_files[0].read_text() == original_content


def test_pop_removes_entry_from_index(dotfiles_dir, sample_files):
    entry = stash_files(dotfiles_dir, "default", sample_files)
    pop_stash(dotfiles_dir, entry.stash_id)
    assert load_index(dotfiles_dir) == []


def test_pop_dry_run_does_not_restore(dotfiles_dir, sample_files):
    entry = stash_files(dotfiles_dir, "default", [sample_files[0]])
    sample_files[0].write_text("changed")
    pop_stash(dotfiles_dir, entry.stash_id, dry_run=True)
    assert sample_files[0].read_text() == "changed"
    assert len(load_index(dotfiles_dir)) == 1


def test_pop_unknown_stash_raises(dotfiles_dir):
    with pytest.raises(StashError, match="Stash not found"):
        pop_stash(dotfiles_dir, "nonexistent_id")


def test_load_index_returns_empty_when_no_file(dotfiles_dir):
    assert load_index(dotfiles_dir) == []
