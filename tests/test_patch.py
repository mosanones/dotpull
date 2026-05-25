"""Tests for dotpull.patch."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch as mock_patch

import pytest

from dotpull.patch import (
    PatchError,
    PatchResult,
    apply_patch,
    apply_patches_for_profile,
    list_patches,
    _patch_dir,
)


@pytest.fixture
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


def test_apply_patch_raises_if_source_missing(tmp_path: Path):
    with pytest.raises(PatchError, match="Source file not found"):
        apply_patch(tmp_path / "missing.txt", tmp_path / "x.patch")


def test_apply_patch_raises_if_patch_missing(tmp_path: Path):
    src = tmp_path / "file.txt"
    src.write_text("hello")
    with pytest.raises(PatchError, match="Patch file not found"):
        apply_patch(src, tmp_path / "missing.patch")


def test_apply_patch_returns_true_on_success(tmp_path: Path):
    src = tmp_path / "file.txt"
    src.write_text("hello")
    pf = tmp_path / "file.patch"
    pf.write_text("")
    with mock_patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        assert apply_patch(src, pf) is True


def test_apply_patch_returns_false_on_failure(tmp_path: Path):
    src = tmp_path / "file.txt"
    src.write_text("hello")
    pf = tmp_path / "file.patch"
    pf.write_text("")
    with mock_patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        assert apply_patch(src, pf) is False


def test_apply_patches_skips_when_no_patch_dir(dotfiles_dir: Path):
    targets = [dotfiles_dir / "bashrc", dotfiles_dir / "vimrc"]
    for t in targets:
        t.write_text("content")
    result = apply_patches_for_profile("work", dotfiles_dir, targets)
    assert result.success
    assert len(result.skipped) == 2
    assert result.patched == []


def test_apply_patches_patches_matching_files(dotfiles_dir: Path):
    patch_root = _patch_dir(dotfiles_dir) / "work"
    patch_root.mkdir(parents=True)
    target = dotfiles_dir / "bashrc"
    target.write_text("content")
    (patch_root / "bashrc.patch").write_text("")

    with mock_patch("dotpull.patch.apply_patch", return_value=True) as mock_ap:
        result = apply_patches_for_profile("work", dotfiles_dir, [target])

    assert result.success
    assert str(target) in result.patched
    mock_ap.assert_called_once()


def test_apply_patches_records_errors_on_bad_patch(dotfiles_dir: Path):
    patch_root = _patch_dir(dotfiles_dir) / "work"
    patch_root.mkdir(parents=True)
    target = dotfiles_dir / "bashrc"
    target.write_text("content")
    (patch_root / "bashrc.patch").write_text("")

    with mock_patch("dotpull.patch.apply_patch", return_value=False):
        result = apply_patches_for_profile("work", dotfiles_dir, [target])

    assert not result.success
    assert len(result.errors) == 1


def test_list_patches_returns_empty_when_no_dir(dotfiles_dir: Path):
    assert list_patches(dotfiles_dir) == []


def test_list_patches_returns_all_patches(dotfiles_dir: Path):
    root = _patch_dir(dotfiles_dir)
    (root / "home").mkdir(parents=True)
    (root / "work").mkdir(parents=True)
    (root / "home" / "bashrc.patch").write_text("")
    (root / "work" / "vimrc.patch").write_text("")
    patches = list_patches(dotfiles_dir)
    assert len(patches) == 2


def test_list_patches_filters_by_profile(dotfiles_dir: Path):
    root = _patch_dir(dotfiles_dir)
    (root / "home").mkdir(parents=True)
    (root / "work").mkdir(parents=True)
    (root / "home" / "bashrc.patch").write_text("")
    (root / "work" / "vimrc.patch").write_text("")
    patches = list_patches(dotfiles_dir, profile_name="home")
    assert len(patches) == 1
    assert patches[0].name == "bashrc.patch"
