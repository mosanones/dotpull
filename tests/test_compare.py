"""Tests for dotpull.compare and dotpull.cli_compare."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from dotpull.compare import compare_profiles, CompareResult


def _make_profile(name, files, variables):
    p = MagicMock()
    p.name = name
    p.files = files
    p.variables = variables
    return p


def test_compare_identical_profiles():
    pa = _make_profile("base", ["a.zsh", "b.zsh"], {"EDITOR": "vim"})
    pb = _make_profile("copy", ["a.zsh", "b.zsh"], {"EDITOR": "vim"})
    result = compare_profiles(pa, pb)
    assert not result.has_differences
    assert result.in_both == ["a.zsh", "b.zsh"]
    assert result.vars_same == {"EDITOR": "vim"}


def test_compare_files_only_in_a():
    pa = _make_profile("base", ["a.zsh", "extra.zsh"], {})
    pb = _make_profile("work", ["a.zsh"], {})
    result = compare_profiles(pa, pb)
    assert result.only_in_a == ["extra.zsh"]
    assert result.only_in_b == []
    assert result.in_both == ["a.zsh"]
    assert result.has_differences


def test_compare_files_only_in_b():
    pa = _make_profile("base", ["a.zsh"], {})
    pb = _make_profile("work", ["a.zsh", "work.zsh"], {})
    result = compare_profiles(pa, pb)
    assert result.only_in_b == ["work.zsh"]
    assert result.only_in_a == []


def test_compare_vars_differ():
    pa = _make_profile("base", [], {"EDITOR": "vim", "THEME": "dark"})
    pb = _make_profile("work", [], {"EDITOR": "emacs", "THEME": "dark"})
    result = compare_profiles(pa, pb)
    assert len(result.vars_differ) == 1
    key, va, vb = result.vars_differ[0]
    assert key == "EDITOR"
    assert va == "vim"
    assert vb == "emacs"
    assert result.vars_same == {"THEME": "dark"}


def test_compare_vars_exclusive():
    pa = _make_profile("base", [], {"ONLY_A": "1"})
    pb = _make_profile("work", [], {"ONLY_B": "2"})
    result = compare_profiles(pa, pb)
    assert result.vars_only_in_a == {"ONLY_A": "1"}
    assert result.vars_only_in_b == {"ONLY_B": "2"}
    assert result.has_differences


def test_summary_includes_profile_names():
    pa = _make_profile("base", ["a.zsh"], {"X": "1"})
    pb = _make_profile("work", ["b.zsh"], {"X": "2"})
    result = compare_profiles(pa, pb)
    summary = result.summary()
    assert "base" in summary
    assert "work" in summary


def test_summary_identical_message():
    pa = _make_profile("base", [], {})
    pb = _make_profile("copy", [], {})
    result = compare_profiles(pa, pb)
    assert "identical" in result.summary().lower()
