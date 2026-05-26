"""Tests for dotpull.preset module."""

import pytest
from pathlib import Path

from dotpull.preset import (
    add_preset,
    remove_preset,
    load_presets,
    apply_preset,
    PresetError,
    Preset,
)


@pytest.fixture
def dotfiles_dir(tmp_path):
    return tmp_path


def test_load_presets_returns_empty_when_no_file(dotfiles_dir):
    result = load_presets(dotfiles_dir)
    assert result == {}


def test_add_preset_creates_entry(dotfiles_dir):
    preset = add_preset(dotfiles_dir, "work", {"EDITOR": "vim", "THEME": "dark"})
    assert preset.name == "work"
    assert preset.variables["EDITOR"] == "vim"


def test_add_preset_persists(dotfiles_dir):
    add_preset(dotfiles_dir, "home", {"SHELL": "zsh"}, description="Home setup")
    loaded = load_presets(dotfiles_dir)
    assert "home" in loaded
    assert loaded["home"].description == "Home setup"
    assert loaded["home"].variables["SHELL"] == "zsh"


def test_add_preset_empty_name_raises(dotfiles_dir):
    with pytest.raises(PresetError, match="empty"):
        add_preset(dotfiles_dir, "", {"KEY": "val"})


def test_add_preset_overwrites_existing(dotfiles_dir):
    add_preset(dotfiles_dir, "work", {"EDITOR": "nano"})
    add_preset(dotfiles_dir, "work", {"EDITOR": "vim"})
    loaded = load_presets(dotfiles_dir)
    assert loaded["work"].variables["EDITOR"] == "vim"


def test_remove_preset_deletes_entry(dotfiles_dir):
    add_preset(dotfiles_dir, "temp", {"X": "1"})
    remove_preset(dotfiles_dir, "temp")
    loaded = load_presets(dotfiles_dir)
    assert "temp" not in loaded


def test_remove_preset_missing_raises(dotfiles_dir):
    with pytest.raises(PresetError, match="not found"):
        remove_preset(dotfiles_dir, "ghost")


def test_apply_preset_merges_variables(dotfiles_dir):
    add_preset(dotfiles_dir, "base", {"EDITOR": "nano", "PAGER": "less"})
    result = apply_preset(dotfiles_dir, "base", {"EDITOR": "vim"})
    assert result["EDITOR"] == "vim"   # profile overrides preset
    assert result["PAGER"] == "less"   # preset fills in missing


def test_apply_preset_missing_raises(dotfiles_dir):
    with pytest.raises(PresetError, match="not found"):
        apply_preset(dotfiles_dir, "nonexistent", {})


def test_preset_roundtrip_to_from_dict():
    p = Preset(name="test", variables={"A": "1"}, description="desc")
    restored = Preset.from_dict(p.to_dict())
    assert restored.name == p.name
    assert restored.variables == p.variables
    assert restored.description == p.description
