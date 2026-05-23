"""Tests for dotpull configuration loading and validation."""

import pytest
from pathlib import Path

from dotpull.config import load_config, validate_config, _default_config


def test_load_config_returns_defaults_when_file_missing(tmp_path):
    missing = tmp_path / "nonexistent.yaml"
    config = load_config(missing)
    defaults = _default_config()
    assert config["active_profile"] == defaults["active_profile"]
    assert config["symlink"] == defaults["symlink"]


def test_load_config_merges_user_values(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("active_profile: work\nsymlink: false\n")
    config = load_config(cfg_file)
    assert config["active_profile"] == "work"
    assert config["symlink"] is False
    assert "backup" in config  # default preserved


def test_load_config_handles_empty_file(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("")
    config = load_config(cfg_file)
    assert config == _default_config()


def test_validate_config_missing_dotfiles_dir(tmp_path):
    config = _default_config()
    config["dotfiles_dir"] = str(tmp_path / "does_not_exist")
    errors = validate_config(config)
    assert any("dotfiles_dir" in e for e in errors)


def test_validate_config_valid(tmp_path):
    config = _default_config()
    config["dotfiles_dir"] = str(tmp_path)
    errors = validate_config(config)
    assert errors == []


def test_validate_config_missing_active_profile(tmp_path):
    config = _default_config()
    config["dotfiles_dir"] = str(tmp_path)
    config["active_profile"] = ""
    errors = validate_config(config)
    assert any("active_profile" in e for e in errors)
