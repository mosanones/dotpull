"""Tests for dotpull.history."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotpull.history import (
    HistoryEntry,
    load_history,
    record_entry,
    make_entry,
    filter_history,
    HISTORY_FILE,
)


@pytest.fixture
def dotfiles_dir(tmp_path: Path) -> Path:
    dotfiles_dir = tmp_path / "dotfiles"
    dotfiles_dir.mkdir()
    return dotfiles_dir


def test_load_history_returns_empty_when_no_file(dotfiles_dir):
    assert load_history(dotfiles_dir) == []


def test_record_and_load_roundtrip(dotfiles_dir):
    entry = make_entry("default", "sync", files_affected=[".bashrc"])
    record_entry(dotfiles_dir, entry)
    loaded = load_history(dotfiles_dir)
    assert len(loaded) == 1
    assert loaded[0].profile == "default"
    assert loaded[0].action == "sync"
    assert ".bashrc" in loaded[0].files_affected


def test_record_multiple_entries(dotfiles_dir):
    record_entry(dotfiles_dir, make_entry("default", "sync"))
    record_entry(dotfiles_dir, make_entry("work", "link"))
    entries = load_history(dotfiles_dir)
    assert len(entries) == 2
    assert entries[1].profile == "work"


def test_load_history_raises_on_corrupt_file(dotfiles_dir):
    (dotfiles_dir / HISTORY_FILE).write_text("not json")
    with pytest.raises(ValueError, match="Corrupt"):
        load_history(dotfiles_dir)


def test_filter_history_by_profile(dotfiles_dir):
    entries = [
        make_entry("default", "sync"),
        make_entry("work", "link"),
        make_entry("default", "rollback"),
    ]
    result = filter_history(entries, profile="default")
    assert all(e.profile == "default" for e in result)
    assert len(result) == 2


def test_filter_history_by_action(dotfiles_dir):
    entries = [
        make_entry("default", "sync"),
        make_entry("work", "link"),
    ]
    result = filter_history(entries, action="link")
    assert len(result) == 1
    assert result[0].action == "link"


def test_filter_history_limit(dotfiles_dir):
    entries = [make_entry("default", "sync") for _ in range(10)]
    result = filter_history(entries, limit=3)
    assert len(result) == 3


def test_make_entry_sets_timestamp():
    entry = make_entry("default", "sync", note="test run")
    assert entry.timestamp
    assert entry.note == "test run"
    assert "T" in entry.timestamp  # ISO format
