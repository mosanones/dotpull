"""Tests for dotpull.snapshot module."""

import json
import pytest
from pathlib import Path

from dotpull.snapshot import (
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    SnapshotError,
    SNAPSHOT_DIR_NAME,
)


@pytest.fixture
def dotfiles_dir(tmp_path):
    d = tmp_path / "dotfiles"
    d.mkdir()
    (d / "bashrc").write_text("export PATH=$PATH:/usr/local/bin")
    (d / "vimrc").write_text('set number\nset tabstop=4\n')
    sub = d / "config" / "git"
    sub.mkdir(parents=True)
    (sub / "config").write_text("[user]\n  name = Test")
    return d


def test_create_snapshot_produces_directory(dotfiles_dir):
    snap = create_snapshot(dotfiles_dir, label="initial")
    assert snap.is_dir()
    assert "initial" in snap.name


def test_create_snapshot_copies_files(dotfiles_dir):
    snap = create_snapshot(dotfiles_dir)
    assert (snap / "bashrc").exists()
    assert (snap / "vimrc").exists()
    assert (snap / "config" / "git" / "config").exists()


def test_create_snapshot_writes_manifest(dotfiles_dir):
    snap = create_snapshot(dotfiles_dir, label="test")
    manifest = json.loads((snap / "manifest.json").read_text())
    assert manifest["label"] == "test"
    assert "bashrc" in manifest["files"]
    assert "vimrc" in manifest["files"]


def test_snapshot_dir_excluded_from_files(dotfiles_dir):
    create_snapshot(dotfiles_dir)
    snap2 = create_snapshot(dotfiles_dir)
    manifest = json.loads((snap2 / "manifest.json").read_text())
    for key in manifest["files"]:
        assert SNAPSHOT_DIR_NAME not in key


def test_list_snapshots_returns_newest_first(dotfiles_dir):
    create_snapshot(dotfiles_dir, label="first")
    create_snapshot(dotfiles_dir, label="second")
    snaps = list_snapshots(dotfiles_dir)
    assert len(snaps) == 2
    assert snaps[0]["label"] == "second"


def test_list_snapshots_empty_when_none(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert list_snapshots(empty_dir) == []


def test_restore_snapshot_overwrites_files(dotfiles_dir):
    snap = create_snapshot(dotfiles_dir, label="before")
    (dotfiles_dir / "bashrc").write_text("# modified")
    restore_snapshot(dotfiles_dir, snap.name)
    assert (dotfiles_dir / "bashrc").read_text() == "export PATH=$PATH:/usr/local/bin"


def test_restore_snapshot_returns_file_list(dotfiles_dir):
    snap = create_snapshot(dotfiles_dir)
    restored = restore_snapshot(dotfiles_dir, snap.name)
    assert "bashrc" in restored
    assert "vimrc" in restored


def test_restore_missing_snapshot_raises(dotfiles_dir):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(dotfiles_dir, "nonexistent_snapshot")
