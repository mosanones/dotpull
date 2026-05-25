"""Tests for dotpull.ignore."""
import pytest
import yaml

from dotpull.ignore import IgnoreStore, IgnoreError, is_ignored


@pytest.fixture
def dotfiles_dir(tmp_path):
    return tmp_path


@pytest.fixture
def store(dotfiles_dir):
    return IgnoreStore(dotfiles_dir=dotfiles_dir)


# --- load / save ---

def test_load_returns_empty_when_no_file(store):
    store.load()
    assert store.list_all() == {}


def test_save_and_load_roundtrip(store, dotfiles_dir):
    store.add("work", "*.swp")
    store.add("work", ".DS_Store")
    store.save()

    store2 = IgnoreStore(dotfiles_dir=dotfiles_dir).load()
    assert store2.patterns_for("work") == ["*.swp", ".DS_Store"]


def test_load_raises_on_invalid_yaml(store, dotfiles_dir):
    (dotfiles_dir / ".dotpullignore").write_text("[unclosed")
    with pytest.raises(IgnoreError, match="Failed to parse"):
        store.load()


def test_load_raises_when_not_mapping(store, dotfiles_dir):
    (dotfiles_dir / ".dotpullignore").write_text("- item1\n- item2\n")
    with pytest.raises(IgnoreError, match="must contain a YAML mapping"):
        store.load()


# --- add / remove ---

def test_add_is_idempotent(store):
    store.add("home", "*.bak")
    store.add("home", "*.bak")
    assert store.patterns_for("home").count("*.bak") == 1


def test_remove_existing_pattern(store):
    store.add("home", "*.bak")
    removed = store.remove("home", "*.bak")
    assert removed is True
    assert "*.bak" not in store.patterns_for("home")


def test_remove_nonexistent_returns_false(store):
    assert store.remove("home", "*.bak") is False


# --- global wildcard profile ---

def test_global_patterns_included_for_all_profiles(store):
    store.add("*", ".DS_Store")
    store.add("work", "*.swp")
    pats = store.patterns_for("work")
    assert ".DS_Store" in pats
    assert "*.swp" in pats


def test_global_patterns_for_unknown_profile(store):
    store.add("*", ".DS_Store")
    assert ".DS_Store" in store.patterns_for("nonexistent")


# --- is_ignored ---

def test_is_ignored_matches_glob(store):
    assert is_ignored("notes.swp", ["*.swp"]) is True


def test_is_ignored_no_match(store):
    assert is_ignored("notes.txt", ["*.swp"]) is False


def test_is_ignored_matches_by_full_path():
    assert is_ignored("subdir/.DS_Store", [".DS_Store"]) is True
