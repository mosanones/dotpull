"""Tests for dotpull.promote."""
from __future__ import annotations

import pytest

from dotpull.profile import Profile
from dotpull.promote import promote_profile, PromoteResult


def _make_profile(name: str, files=None, variables=None) -> Profile:
    return Profile(
        name=name,
        files=files or {},
        variables=variables or {},
    )


def test_promote_merges_files():
    src = _make_profile("dev", files={"bashrc": "~/.bashrc", "vimrc": "~/.vimrc"})
    tgt = _make_profile("prod", files={})
    result = promote_profile(src, tgt)
    assert "bashrc" in tgt.files
    assert "vimrc" in tgt.files
    assert result.merged_files == ["bashrc", "vimrc"]
    assert result.skipped_files == []


def test_promote_merges_variables():
    src = _make_profile("dev", variables={"editor": "nvim", "theme": "dark"})
    tgt = _make_profile("prod", variables={})
    result = promote_profile(src, tgt)
    assert tgt.variables["editor"] == "nvim"
    assert tgt.variables["theme"] == "dark"
    assert set(result.merged_vars) == {"editor", "theme"}


def test_promote_skips_existing_files_without_overwrite():
    src = _make_profile("dev", files={"bashrc": "~/.bashrc"})
    tgt = _make_profile("prod", files={"bashrc": "~/.bashrc.prod"})
    result = promote_profile(src, tgt, overwrite=False)
    assert tgt.files["bashrc"] == "~/.bashrc.prod"  # unchanged
    assert result.skipped_files == ["bashrc"]
    assert result.merged_files == []


def test_promote_overwrites_existing_files_with_flag():
    src = _make_profile("dev", files={"bashrc": "~/.bashrc"})
    tgt = _make_profile("prod", files={"bashrc": "~/.bashrc.prod"})
    result = promote_profile(src, tgt, overwrite=True)
    assert tgt.files["bashrc"] == "~/.bashrc"  # overwritten
    assert result.merged_files == ["bashrc"]
    assert result.skipped_files == []


def test_promote_skips_existing_vars_without_overwrite():
    src = _make_profile("dev", variables={"editor": "nvim"})
    tgt = _make_profile("prod", variables={"editor": "vim"})
    result = promote_profile(src, tgt, overwrite=False)
    assert tgt.variables["editor"] == "vim"
    assert result.skipped_vars == ["editor"]


def test_promote_result_summary_contains_counts():
    src = _make_profile("dev", files={"a": "~/a"}, variables={"x": "1"})
    tgt = _make_profile("prod")
    result = promote_profile(src, tgt)
    summary = result.summary()
    assert "files merged:   1" in summary
    assert "vars merged:    1" in summary


def test_promote_result_healthy():
    src = _make_profile("dev")
    tgt = _make_profile("prod")
    result = promote_profile(src, tgt)
    assert result.healthy() is True


def test_promote_empty_source_leaves_target_unchanged():
    src = _make_profile("dev")
    tgt = _make_profile("prod", files={"zshrc": "~/.zshrc"}, variables={"shell": "zsh"})
    result = promote_profile(src, tgt)
    assert tgt.files == {"zshrc": "~/.zshrc"}
    assert tgt.variables == {"shell": "zsh"}
    assert result.merged_files == []
    assert result.merged_vars == []
