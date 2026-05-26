"""Tests for dotpull.group."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotpull.group import GroupError, GroupStore, load_groups


@pytest.fixture
def dotfiles_dir(tmp_path):
    return tmp_path


def test_load_returns_empty_when_no_file(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    assert store.all_groups() == []


def test_add_and_members(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    store.add("work", "base")
    store.add("work", "dev")
    assert store.members("work") == ["base", "dev"]


def test_add_idempotent(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    store.add("work", "base")
    store.add("work", "base")
    assert store.members("work") == ["base"]


def test_add_empty_group_raises(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    with pytest.raises(GroupError, match="Group name"):
        store.add("", "base")


def test_add_empty_profile_raises(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    with pytest.raises(GroupError, match="Profile name"):
        store.add("work", "")


def test_remove_existing_profile(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    store.add("work", "base")
    removed = store.remove("work", "base")
    assert removed is True
    assert store.members("work") == []
    assert "work" not in store.all_groups()


def test_remove_nonexistent_profile_returns_false(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    store.add("work", "base")
    removed = store.remove("work", "missing")
    assert removed is False


def test_delete_group(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    store.add("work", "base")
    deleted = store.delete_group("work")
    assert deleted is True
    assert store.all_groups() == []


def test_delete_missing_group_returns_false(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    assert store.delete_group("nonexistent") is False


def test_groups_for_profile(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    store.add("work", "base")
    store.add("personal", "base")
    store.add("personal", "home")
    assert sorted(store.groups_for_profile("base")) == ["personal", "work"]
    assert store.groups_for_profile("home") == ["personal"]


def test_save_and_load_roundtrip(dotfiles_dir):
    store = load_groups(dotfiles_dir)
    store.add("work", "base")
    store.add("work", "dev")
    store.save()

    store2 = load_groups(dotfiles_dir)
    assert store2.members("work") == ["base", "dev"]
