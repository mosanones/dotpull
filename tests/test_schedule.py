"""Tests for dotpull.schedule."""
from __future__ import annotations

import json
import time
import pytest
from pathlib import Path

from dotpull.schedule import ScheduleEntry, ScheduleStore, ScheduleError, run_due


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / ".dotpull" / "schedule.json"


@pytest.fixture
def populated_store() -> ScheduleStore:
    """Return a ScheduleStore pre-populated with two enabled entries."""
    store = ScheduleStore()
    store.add("default", 300)
    store.add("work", 60)
    return store


def test_load_returns_empty_when_no_file(store_path):
    store = ScheduleStore.load(store_path)
    assert store.entries == {}


def test_add_creates_entry():
    store = ScheduleStore()
    entry = store.add("default", 300)
    assert entry.profile == "default"
    assert entry.interval_seconds == 300
    assert entry.enabled is True
    assert entry.last_run is None


def test_add_invalid_interval_raises():
    store = ScheduleStore()
    with pytest.raises(ScheduleError, match="positive"):
        store.add("default", 0)


def test_remove_existing_entry():
    store = ScheduleStore()
    store.add("work", 60)
    store.remove("work")
    assert "work" not in store.entries


def test_remove_missing_raises():
    store = ScheduleStore()
    with pytest.raises(ScheduleError, match="No schedule"):
        store.remove("nonexistent")


def test_save_and_load_roundtrip(store_path):
    store = ScheduleStore()
    store.add("home", 120)
    store.save(store_path)
    loaded = ScheduleStore.load(store_path)
    assert "home" in loaded.entries
    assert loaded.entries["home"].interval_seconds == 120


def test_due_returns_entries_with_no_last_run():
    store = ScheduleStore()
    store.add("default", 300)
    due = store.due(now=time.time())
    assert len(due) == 1
    assert due[0].profile == "default"


def test_due_skips_recently_run():
    store = ScheduleStore()
    store.add("default", 300)
    now = time.time()
    store.mark_run("default", now=now)
    due = store.due(now=now + 10)
    assert due == []


def test_due_includes_overdue_entry():
    store = ScheduleStore()
    store.add("default", 300)
    past = time.time() - 400
    store.mark_run("default", now=past)
    due = store.due(now=time.time())
    assert len(due) == 1


def test_due_skips_disabled_entries():
    store = ScheduleStore()
    store.add("default", 60)
    store.entries["default"].enabled = False
    assert store.due() == []


def test_run_due_calls_on_sync_and_marks():
    store = ScheduleStore()
    store.add("alpha", 60)
    store.add("beta", 60)
    called = []
    now = time.time()
    ran = run_due(store, on_sync=lambda p: called.append(p), now=now)
    assert set(ran) == {"alpha", "beta"}
    assert set(called) == {"alpha", "beta"}
    assert store.entries["alpha"].last_run == now
    assert store.entries["beta"].last_run == now


def test_run_due_returns_empty_when_nothing_due(populated_store):
    """run_due should return an empty list when all entries were just run."""
    now = time.time()
    for profile in populated_store.entries:
        populated_store.mark_run(profile, now=now)
    ran = run_due(populated_store, on_sync=lambda p: None, now=now + 1)
    assert ran == []
