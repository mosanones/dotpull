"""Tests for dotpull.diff module."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotpull.diff import DiffResult, diff_file, diff_profile_files


@pytest.fixture
def tmp_files(tmp_path: Path):
    source = tmp_path / "dotfiles" / ".bashrc"
    source.parent.mkdir(parents=True)
    target = tmp_path / "home" / ".bashrc"
    target.parent.mkdir(parents=True)
    return source, target


def test_diff_file_missing_source(tmp_files):
    source, target = tmp_files
    target.write_text("echo hi\n")
    result = diff_file(source, target)
    assert result.status == "missing_source"
    assert result.unified_diff == []


def test_diff_file_missing_target(tmp_files):
    source, target = tmp_files
    source.write_text("echo hi\n")
    result = diff_file(source, target)
    assert result.status == "missing_target"


def test_diff_file_symlink_same(tmp_files):
    source, target = tmp_files
    source.write_text("export PATH=~/.local/bin:$PATH\n")
    target.symlink_to(source)
    result = diff_file(source, target)
    assert result.status == "same"
    assert result.unified_diff == []


def test_diff_file_content_same_no_symlink(tmp_files):
    source, target = tmp_files
    content = "alias ll='ls -la'\n"
    source.write_text(content)
    target.write_text(content)
    result = diff_file(source, target)
    assert result.status == "same"


def test_diff_file_content_differs(tmp_files):
    source, target = tmp_files
    source.write_text("alias ll='ls -la'\n")
    target.write_text("alias ll='ls -l'\n")
    result = diff_file(source, target)
    assert result.status == "differs"
    assert any("+alias ll='ls -la'" in line for line in result.unified_diff)


def test_diff_profile_files_mixed(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    (dotfiles / ".vimrc").write_text("set number\n")
    (home / ".vimrc").write_text("set nonumber\n")

    (dotfiles / ".tmux.conf").write_text("set -g mouse on\n")
    # target missing intentionally

    file_map = {
        ".vimrc": str(home / ".vimrc"),
        ".tmux.conf": str(home / ".tmux.conf"),
    }

    results = diff_profile_files(dotfiles, file_map, home_dir=home)
    assert len(results) == 2

    statuses = {r.source.name: r.status for r in results}
    assert statuses[".vimrc"] == "differs"
    assert statuses[".tmux.conf"] == "missing_target"


def test_diff_profile_files_relative_target(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    content = "export EDITOR=vim\n"
    (dotfiles / ".profile").write_text(content)
    (home / ".profile").write_text(content)

    results = diff_profile_files(
        dotfiles, {".profile": ".profile"}, home_dir=home
    )
    assert results[0].status == "same"
