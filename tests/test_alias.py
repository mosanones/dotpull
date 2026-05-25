"""Unit tests for dotpull.alias."""
from __future__ import annotations

import pytest

from dotpull.alias import AliasError, AliasStore, load, resolve_alias


@pytest.fixture()
def dotfiles_dir(tmp_path):
    return tmp_path


# ---------------------------------------------------------------------------
# AliasStore unit tests
# ---------------------------------------------------------------------------

def test_load_returns_empty_when_no_file(dotfiles_dir):
    store = load(dotfiles_dir)
    assert store.all() == {}


def test_set_and_get_roundtrip(dotfiles_dir):
    store = load(dotfiles_dir)
    store.set("work", "work-linux")
    assert store.get("work") == "work-linux"


def test_set_empty_name_raises(dotfiles_dir):
    store = load(dotfiles_dir)
    with pytest.raises(AliasError):
        store.set("", "some-profile")


def test_set_empty_profile_raises(dotfiles_dir):
    store = load(dotfiles_dir)
    with pytest.raises(AliasError):
        store.set("myalias", "")


def test_remove_existing_returns_true(dotfiles_dir):
    store = load(dotfiles_dir)
    store.set("home", "home-profile")
    assert store.remove("home") is True
    assert store.get("home") is None


def test_remove_missing_returns_false(dotfiles_dir):
    store = load(dotfiles_dir)
    assert store.remove("ghost") is False


def test_save_and_reload(dotfiles_dir):
    store = load(dotfiles_dir)
    store.set("dev", "dev-profile")
    store.set("prod", "prod-profile")
    store.save()

    reloaded = load(dotfiles_dir)
    assert reloaded.get("dev") == "dev-profile"
    assert reloaded.get("prod") == "prod-profile"


def test_load_raises_on_invalid_yaml(dotfiles_dir):
    alias_file = dotfiles_dir / ".dotpull" / "aliases.yaml"
    alias_file.parent.mkdir(parents=True)
    alias_file.write_text(": invalid: [yaml")
    with pytest.raises(AliasError):
        load(dotfiles_dir)


def test_load_raises_on_non_mapping(dotfiles_dir):
    alias_file = dotfiles_dir / ".dotpull" / "aliases.yaml"
    alias_file.parent.mkdir(parents=True)
    alias_file.write_text("- item1\n- item2\n")
    with pytest.raises(AliasError):
        load(dotfiles_dir)


# ---------------------------------------------------------------------------
# resolve_alias
# ---------------------------------------------------------------------------

def test_resolve_alias_known(dotfiles_dir):
    store = load(dotfiles_dir)
    store.set("w", "work-linux")
    assert resolve_alias(store, "w") == "work-linux"


def test_resolve_alias_unknown_returns_name(dotfiles_dir):
    store = load(dotfiles_dir)
    assert resolve_alias(store, "unknown") == "unknown"
