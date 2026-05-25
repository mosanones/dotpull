"""Tests for dotpull.search."""
from __future__ import annotations

import pytest

from dotpull.search import search_profiles, search_files_by_extension, SearchResult


class _FakeProfile:
    def __init__(self, files=None, variables=None):
        self.files = files or {}
        self.variables = variables or {}


@pytest.fixture()
def profiles():
    return {
        "base": _FakeProfile(
            files={"bashrc": "~/.bashrc", "vimrc": "~/.vimrc"},
            variables={"editor": "vim", "shell": "bash"},
        ),
        "work": _FakeProfile(
            files={"gitconfig": "~/.gitconfig", "zshrc": "~/.zshrc"},
            variables={"git_email": "work@example.com"},
        ),
        "empty": _FakeProfile(),
    }


def test_search_finds_file_by_substring(profiles):
    results = search_profiles(profiles, "vim")
    assert len(results) == 1
    assert results[0].profile_name == "base"
    assert "vimrc" in results[0].matched_files


def test_search_finds_variable_by_name(profiles):
    results = search_profiles(profiles, "email")
    assert len(results) == 1
    assert results[0].profile_name == "work"
    assert "git_email" in results[0].matched_variables


def test_search_case_insensitive_by_default(profiles):
    results = search_profiles(profiles, "BASH")
    assert any(r.profile_name == "base" for r in results)


def test_search_case_sensitive_no_match(profiles):
    results = search_profiles(profiles, "BASH", case_sensitive=True)
    assert results == []


def test_search_no_files_skips_file_matching(profiles):
    results = search_profiles(profiles, "vimrc", search_files=False)
    assert results == []


def test_search_no_vars_skips_variable_matching(profiles):
    results = search_profiles(profiles, "editor", search_variables=False)
    assert results == []


def test_search_empty_profile_not_included(profiles):
    results = search_profiles(profiles, "anything")
    assert all(r.profile_name != "empty" for r in results)


def test_search_by_extension_toml(profiles):
    profiles["base"].files["config.toml"] = "~/.config/app/config.toml"
    results = search_files_by_extension(profiles, "toml")
    assert len(results) == 1
    assert results[0].profile_name == "base"


def test_search_by_extension_with_leading_dot(profiles):
    profiles["work"].files["app.yaml"] = "~/.config/app.yaml"
    results = search_files_by_extension(profiles, ".yaml")
    assert results[0].profile_name == "work"


def test_search_by_extension_no_match(profiles):
    results = search_files_by_extension(profiles, "rs")
    assert results == []
