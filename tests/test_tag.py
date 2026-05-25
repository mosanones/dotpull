"""Tests for dotpull.tag."""

from __future__ import annotations

import pytest
from pathlib import Path

from dotpull.tag import TagError, TagStore, load_tag_store


@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


@pytest.fixture()
def store(dotfiles_dir: Path) -> TagStore:
    return load_tag_store(dotfiles_dir)


def test_load_returns_empty_when_no_file(store: TagStore):
    assert store.tags_for("work") == []
    assert store.all_tags() == []


def test_add_tag_and_retrieve(store: TagStore):
    store.add_tag("work", "laptop")
    assert "laptop" in store.tags_for("work")


def test_add_tag_idempotent(store: TagStore):
    store.add_tag("work", "laptop")
    store.add_tag("work", "laptop")
    assert store.tags_for("work").count("laptop") == 1


def test_remove_tag_removes_entry(store: TagStore):
    store.add_tag("work", "laptop")
    store.remove_tag("work", "laptop")
    assert "laptop" not in store.tags_for("work")


def test_remove_tag_cleans_empty_profile(store: TagStore):
    store.add_tag("work", "laptop")
    store.remove_tag("work", "laptop")
    assert "work" not in store._data


def test_remove_missing_tag_raises(store: TagStore):
    with pytest.raises(TagError, match="does not have tag"):
        store.remove_tag("work", "nonexistent")


def test_profiles_for_tag(store: TagStore):
    store.add_tag("work", "laptop")
    store.add_tag("home", "laptop")
    store.add_tag("server", "remote")
    profiles = store.profiles_for("laptop")
    assert "work" in profiles
    assert "home" in profiles
    assert "server" not in profiles


def test_all_tags_unique(store: TagStore):
    store.add_tag("work", "laptop")
    store.add_tag("home", "laptop")
    store.add_tag("server", "remote")
    all_tags = store.all_tags()
    assert all_tags.count("laptop") == 1
    assert "remote" in all_tags


def test_save_and_load_roundtrip(dotfiles_dir: Path):
    store = load_tag_store(dotfiles_dir)
    store.add_tag("work", "laptop")
    store.add_tag("work", "office")
    store.save()

    store2 = load_tag_store(dotfiles_dir)
    assert "laptop" in store2.tags_for("work")
    assert "office" in store2.tags_for("work")
