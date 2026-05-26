"""Tests for dotpull.freeze."""
from __future__ import annotations

import json
import time

import pytest

from dotpull.freeze import (
    FreezeEntry,
    FreezeError,
    freeze_profile,
    list_freezes,
    load_freezes,
    save_freezes,
)


@pytest.fixture()
def dotfiles_dir(tmp_path):
    return tmp_path


def test_load_freezes_returns_empty_when_no_file(dotfiles_dir):
    result = load_freezes(dotfiles_dir)
    assert result == []


def test_freeze_profile_creates_entry(dotfiles_dir):
    entry = freeze_profile(dotfiles_dir, "work", {"EDITOR": "vim"}, label="initial")
    assert entry.profile == "work"
    assert entry.variables == {"EDITOR": "vim"}
    assert entry.label == "initial"
    assert entry.timestamp <= time.time()


def test_freeze_profile_persists_to_disk(dotfiles_dir):
    freeze_profile(dotfiles_dir, "home", {"SHELL": "zsh"})
    loaded = load_freezes(dotfiles_dir)
    assert len(loaded) == 1
    assert loaded[0].profile == "home"
    assert loaded[0].variables == {"SHELL": "zsh"}


def test_freeze_profile_appends_multiple_entries(dotfiles_dir):
    freeze_profile(dotfiles_dir, "work", {"A": "1"})
    freeze_profile(dotfiles_dir, "work", {"A": "2"})
    entries = load_freezes(dotfiles_dir)
    assert len(entries) == 2
    assert entries[0].variables["A"] == "1"
    assert entries[1].variables["A"] == "2"


def test_freeze_profile_empty_name_raises(dotfiles_dir):
    with pytest.raises(FreezeError, match="profile name"):
        freeze_profile(dotfiles_dir, "", {"X": "y"})


def test_list_freezes_filters_by_profile(dotfiles_dir):
    freeze_profile(dotfiles_dir, "work", {"A": "1"})
    freeze_profile(dotfiles_dir, "home", {"B": "2"})
    freeze_profile(dotfiles_dir, "work", {"A": "3"})
    result = list_freezes(dotfiles_dir, profile="work")
    assert len(result) == 2
    assert all(e.profile == "work" for e in result)


def test_list_freezes_no_filter_returns_all(dotfiles_dir):
    freeze_profile(dotfiles_dir, "work", {})
    freeze_profile(dotfiles_dir, "home", {})
    assert len(list_freezes(dotfiles_dir)) == 2


def test_load_freezes_raises_on_corrupt_file(dotfiles_dir):
    path = dotfiles_dir / ".dotpull" / "freezes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not valid json{{{")
    with pytest.raises(FreezeError):
        load_freezes(dotfiles_dir)


def test_freeze_entry_roundtrip():
    entry = FreezeEntry(profile="p", timestamp=1234.5, variables={"K": "V"}, label="lbl")
    restored = FreezeEntry.from_dict(entry.to_dict())
    assert restored.profile == entry.profile
    assert restored.timestamp == entry.timestamp
    assert restored.variables == entry.variables
    assert restored.label == entry.label
