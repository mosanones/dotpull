"""Tests for dotpull.rollback."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from dotpull.rollback import rollback_profile, list_rollback_targets
from dotpull.snapshot import SnapshotError, _snapshot_dir


@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


def _make_snapshot(dotfiles_dir: Path, label: str, files: dict[str, str]) -> Path:
    """Helper: create a fake snapshot with given file contents."""
    snap = _snapshot_dir(dotfiles_dir) / label
    snap.mkdir(parents=True)
    manifest_files = []
    for rel, content in files.items():
        f = snap / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
        manifest_files.append({"path": rel})
    (snap / "manifest.json").write_text(json.dumps({"files": manifest_files}))
    return snap


def test_rollback_restores_files(dotfiles_dir: Path):
    _make_snapshot(dotfiles_dir, "snap-01", {"bashrc": "# restored", "vimrc": "set nu"})
    result = rollback_profile(dotfiles_dir, "default", "snap-01")
    assert result.success
    assert "bashrc" in result.restored
    assert "vimrc" in result.restored
    assert (dotfiles_dir / "bashrc").read_text() == "# restored"


def test_rollback_dry_run_does_not_write(dotfiles_dir: Path):
    _make_snapshot(dotfiles_dir, "snap-02", {"zshrc": "# zsh"})
    result = rollback_profile(dotfiles_dir, "default", "snap-02", dry_run=True)
    assert result.success
    assert "zshrc" in result.restored
    assert not (dotfiles_dir / "zshrc").exists()


def test_rollback_missing_snapshot_raises(dotfiles_dir: Path):
    with pytest.raises(SnapshotError, match="not found"):
        rollback_profile(dotfiles_dir, "default", "nonexistent")


def test_rollback_skips_missing_snapshot_file(dotfiles_dir: Path):
    snap = _make_snapshot(dotfiles_dir, "snap-03", {"bashrc": "x"})
    manifest = json.loads((snap / "manifest.json").read_text())
    manifest["files"].append({"path": "ghost_file"})
    (snap / "manifest.json").write_text(json.dumps(manifest))

    result = rollback_profile(dotfiles_dir, "default", "snap-03")
    assert "ghost_file" in result.skipped
    assert result.success


def test_list_rollback_targets_newest_first(dotfiles_dir: Path):
    for label in ["2024-01-01", "2024-03-01", "2024-02-01"]:
        _make_snapshot(dotfiles_dir, label, {})
    targets = list_rollback_targets(dotfiles_dir)
    assert targets == ["2024-03-01", "2024-02-01", "2024-01-01"]


def test_list_rollback_targets_empty_when_no_snapshots(dotfiles_dir: Path):
    targets = list_rollback_targets(dotfiles_dir)
    assert targets == []
