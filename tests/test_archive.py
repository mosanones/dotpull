"""Tests for dotpull.archive."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from dotpull.archive import (
    ArchiveError,
    ArchiveResult,
    create_archive,
    list_archives,
    restore_archive,
)


@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    (d / "bashrc").write_text("export PATH=$PATH:/usr/local/bin\n")
    (d / "vimrc").write_text('set number\nset tabstop=4\n')
    sub = d / "config" / "git"
    sub.mkdir(parents=True)
    (sub / "gitconfig").write_text("[user]\n  name = Test\n")
    return d


def test_create_archive_produces_file(dotfiles_dir: Path):
    result = create_archive(dotfiles_dir)
    assert result.path.exists()
    assert result.path.suffix == ".gz"
    assert tarfile.is_tarfile(result.path)


def test_create_archive_contains_files(dotfiles_dir: Path):
    result = create_archive(dotfiles_dir)
    assert "bashrc" in result.files
    assert "vimrc" in result.files
    assert "config/git/gitconfig" in result.files


def test_create_archive_excludes_archive_dir(dotfiles_dir: Path):
    # Create a first archive so .archives/ exists
    create_archive(dotfiles_dir)
    result = create_archive(dotfiles_dir, label="second")
    assert not any(".archives" in f for f in result.files)


def test_create_archive_has_checksum(dotfiles_dir: Path):
    result = create_archive(dotfiles_dir)
    assert len(result.checksum) == 64  # sha256 hex
    assert result.healthy


def test_create_archive_with_label(dotfiles_dir: Path):
    result = create_archive(dotfiles_dir, label="mybackup")
    assert "mybackup" in result.label
    assert "mybackup" in result.path.name


def test_create_archive_missing_dir_raises(tmp_path: Path):
    with pytest.raises(ArchiveError, match="not found"):
        create_archive(tmp_path / "nonexistent")


def test_list_archives_empty_when_none(dotfiles_dir: Path):
    assert list_archives(dotfiles_dir) == []


def test_list_archives_returns_entries(dotfiles_dir: Path):
    create_archive(dotfiles_dir, label="a")
    create_archive(dotfiles_dir, label="b")
    entries = list_archives(dotfiles_dir)
    assert len(entries) == 2
    assert all(isinstance(e, ArchiveResult) for e in entries)


def test_restore_archive_extracts_files(dotfiles_dir: Path, tmp_path: Path):
    result = create_archive(dotfiles_dir)
    target = tmp_path / "restored"
    restored = restore_archive(result.path, target)
    assert "bashrc" in restored
    assert (target / "bashrc").read_text() == "export PATH=$PATH:/usr/local/bin\n"


def test_restore_archive_skips_existing_without_overwrite(dotfiles_dir: Path, tmp_path: Path):
    result = create_archive(dotfiles_dir)
    target = tmp_path / "restored"
    target.mkdir()
    (target / "bashrc").write_text("original")
    restored = restore_archive(result.path, target, overwrite=False)
    assert "bashrc" not in restored
    assert (target / "bashrc").read_text() == "original"


def test_restore_archive_missing_raises(tmp_path: Path):
    with pytest.raises(ArchiveError, match="not found"):
        restore_archive(tmp_path / "ghost.tar.gz", tmp_path / "out")
