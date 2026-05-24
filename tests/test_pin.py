"""Tests for dotpull.pin module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from dotpull.pin import (
    pin_profile,
    unpin_profile,
    list_pins,
    load_pins,
    save_pins,
    PinStore,
    PinEntry,
    PinError,
    PIN_FILE,
)


@pytest.fixture
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


def _fake_snapshots(names: list[str]) -> list[dict]:
    return [{"name": n, "files": []} for n in names]


def test_load_pins_returns_empty_when_no_file(dotfiles_dir: Path) -> None:
    store = load_pins(dotfiles_dir)
    assert store.pins == {}


def test_save_and_load_roundtrip(dotfiles_dir: Path) -> None:
    store = PinStore()
    store.set(PinEntry(profile="work", snapshot="snap-001", created_at="2024-01-01T00:00:00+00:00", note="stable"))
    save_pins(dotfiles_dir, store)
    loaded = load_pins(dotfiles_dir)
    assert "work" in loaded.pins
    assert loaded.pins["work"].snapshot == "snap-001"
    assert loaded.pins["work"].note == "stable"


def test_pin_profile_creates_entry(dotfiles_dir: Path) -> None:
    with patch("dotpull.pin.list_snapshots", return_value=_fake_snapshots(["snap-001", "snap-002"])):
        entry = pin_profile(dotfiles_dir, "home", "snap-001", note="initial")
    assert entry.profile == "home"
    assert entry.snapshot == "snap-001"
    assert entry.note == "initial"
    assert (dotfiles_dir / PIN_FILE).exists()


def test_pin_profile_raises_on_unknown_snapshot(dotfiles_dir: Path) -> None:
    with patch("dotpull.pin.list_snapshots", return_value=_fake_snapshots(["snap-001"])):
        with pytest.raises(PinError, match="snap-999"):
            pin_profile(dotfiles_dir, "home", "snap-999")


def test_pin_profile_overwrites_existing(dotfiles_dir: Path) -> None:
    with patch("dotpull.pin.list_snapshots", return_value=_fake_snapshots(["snap-001", "snap-002"])):
        pin_profile(dotfiles_dir, "home", "snap-001")
        pin_profile(dotfiles_dir, "home", "snap-002")
    store = load_pins(dotfiles_dir)
    assert store.pins["home"].snapshot == "snap-002"


def test_unpin_profile_removes_entry(dotfiles_dir: Path) -> None:
    with patch("dotpull.pin.list_snapshots", return_value=_fake_snapshots(["snap-001"])):
        pin_profile(dotfiles_dir, "work", "snap-001")
    removed = unpin_profile(dotfiles_dir, "work")
    assert removed is True
    assert list_pins(dotfiles_dir) == []


def test_unpin_profile_returns_false_when_not_pinned(dotfiles_dir: Path) -> None:
    removed = unpin_profile(dotfiles_dir, "nonexistent")
    assert removed is False


def test_list_pins_returns_all_entries(dotfiles_dir: Path) -> None:
    with patch("dotpull.pin.list_snapshots", return_value=_fake_snapshots(["s1", "s2"])):
        pin_profile(dotfiles_dir, "home", "s1")
        pin_profile(dotfiles_dir, "work", "s2")
    pins = list_pins(dotfiles_dir)
    profiles = {p.profile for p in pins}
    assert profiles == {"home", "work"}
