"""Tests for dotpull.copy."""
from __future__ import annotations

import pytest
from pathlib import Path

from dotpull.copy import CopyError, copy_into_repo


@pytest.fixture()
def tmp_files(tmp_path: Path):
    src_dir = tmp_path / "home" / "user"
    src_dir.mkdir(parents=True)
    repo = tmp_path / "dotfiles"
    repo.mkdir()
    return src_dir, repo


def test_copy_places_file_in_repo(tmp_files):
    src_dir, repo = tmp_files
    src = src_dir / ".bashrc"
    src.write_text("# bash")

    result = copy_into_repo(src, repo, relative_dest=".bashrc")

    assert result.healthy
    assert (repo / ".bashrc").read_text() == "# bash"
    assert result.backed_up is None


def test_copy_mirrors_absolute_path(tmp_files):
    src_dir, repo = tmp_files
    src = src_dir / ".vimrc"
    src.write_text("set number")

    result = copy_into_repo(src, repo)

    # destination mirrors stripped absolute path
    assert result.destination.is_relative_to(repo)
    assert result.destination.read_text() == "set number"


def test_copy_raises_if_source_missing(tmp_files):
    _, repo = tmp_files
    with pytest.raises(CopyError, match="does not exist"):
        copy_into_repo(Path("/no/such/file"), repo)


def test_copy_raises_if_source_is_directory(tmp_files):
    src_dir, repo = tmp_files
    with pytest.raises(CopyError, match="directory"):
        copy_into_repo(src_dir, repo)


def test_copy_raises_on_existing_without_overwrite(tmp_files):
    src_dir, repo = tmp_files
    src = src_dir / ".tmux.conf"
    src.write_text("new")
    (repo / ".tmux.conf").write_text("old")

    with pytest.raises(CopyError, match="already exists"):
        copy_into_repo(src, repo, relative_dest=".tmux.conf")


def test_copy_overwrites_and_backs_up(tmp_files):
    src_dir, repo = tmp_files
    src = src_dir / ".tmux.conf"
    src.write_text("new")
    existing = repo / ".tmux.conf"
    existing.write_text("old")

    result = copy_into_repo(src, repo, relative_dest=".tmux.conf", overwrite=True)

    assert existing.read_text() == "new"
    assert result.backed_up is not None
    assert result.backed_up.read_text() == "old"


def test_copy_dry_run_does_not_write(tmp_files):
    src_dir, repo = tmp_files
    src = src_dir / ".zshrc"
    src.write_text("zsh")

    result = copy_into_repo(src, repo, relative_dest=".zshrc", dry_run=True)

    assert result.skipped
    assert not (repo / ".zshrc").exists()


def test_copy_creates_parent_dirs(tmp_files):
    src_dir, repo = tmp_files
    src = src_dir / "nested.conf"
    src.write_text("data")

    result = copy_into_repo(src, repo, relative_dest="config/nested/nested.conf")

    assert (repo / "config" / "nested" / "nested.conf").exists()
    assert result.healthy
