"""Tests for dotpull.rename."""

import pytest
from pathlib import Path

from dotpull.rename import rename_dotfile, rename_dotfiles, RenameResult


@pytest.fixture
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


def _touch(base: Path, rel: str) -> Path:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("content")
    return p


def test_rename_moves_file(dotfiles_dir: Path) -> None:
    _touch(dotfiles_dir, "bashrc")
    result = rename_dotfile(dotfiles_dir, "bashrc", "bash/bashrc")
    assert result.success
    assert not (dotfiles_dir / "bashrc").exists()
    assert (dotfiles_dir / "bash" / "bashrc").exists()


def test_rename_creates_parent_dirs(dotfiles_dir: Path) -> None:
    _touch(dotfiles_dir, "vimrc")
    result = rename_dotfile(dotfiles_dir, "vimrc", "editors/vim/vimrc")
    assert result.success
    assert (dotfiles_dir / "editors" / "vim" / "vimrc").exists()


def test_rename_missing_source_fails(dotfiles_dir: Path) -> None:
    result = rename_dotfile(dotfiles_dir, "nonexistent", "other")
    assert not result.success
    assert "source not found" in result.message


def test_rename_existing_destination_fails(dotfiles_dir: Path) -> None:
    _touch(dotfiles_dir, "a")
    _touch(dotfiles_dir, "b")
    result = rename_dotfile(dotfiles_dir, "a", "b")
    assert not result.success
    assert "already exists" in result.message


def test_rename_dry_run_does_not_move(dotfiles_dir: Path) -> None:
    _touch(dotfiles_dir, "zshrc")
    result = rename_dotfile(dotfiles_dir, "zshrc", "zsh/zshrc", dry_run=True)
    assert result.success
    assert "dry-run" in result.message
    assert (dotfiles_dir / "zshrc").exists()
    assert not (dotfiles_dir / "zsh" / "zshrc").exists()


def test_rename_dotfiles_batch(dotfiles_dir: Path) -> None:
    _touch(dotfiles_dir, "a")
    _touch(dotfiles_dir, "b")
    summary = rename_dotfiles(dotfiles_dir, [("a", "x"), ("b", "y")])
    assert summary.healthy
    assert len(summary.results) == 2
    assert (dotfiles_dir / "x").exists()
    assert (dotfiles_dir / "y").exists()


def test_rename_summary_not_healthy_on_failure(dotfiles_dir: Path) -> None:
    _touch(dotfiles_dir, "a")
    summary = rename_dotfiles(dotfiles_dir, [("a", "ok"), ("missing", "fail")])
    assert not summary.healthy
    assert "1 renamed, 1 failed" == summary.summary


def test_rename_result_fields() -> None:
    r = RenameResult(old_path="old", new_path="new", success=True, message="done")
    assert r.old_path == "old"
    assert r.new_path == "new"
    assert r.success is True
