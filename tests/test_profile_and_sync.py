"""Tests for profile resolution and sync logic."""

import pytest
from pathlib import Path

from dotpull.profile import Profile, resolve_profile
from dotpull.sync import sync_profile


@pytest.fixture
def dotfiles_dir(tmp_path):
    d = tmp_path / "dotfiles"
    d.mkdir()
    (d / "vimrc").write_text('set number\n')
    (d / "bashrc").write_text('export PATH=$PATH:~/bin\n')
    return d


@pytest.fixture
def base_config(dotfiles_dir, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    return {
        "dotfiles_dir": str(dotfiles_dir),
        "active_profile": "default",
        "profiles": {
            "default": {
                "files": {
                    "vimrc": str(home / ".vimrc"),
                    "bashrc": str(home / ".bashrc"),
                }
            },
            "work": {
                "extends": "default",
                "files": {
                    "bashrc": str(home / ".bashrc_work"),
                },
            },
        },
    }


def test_resolve_profile_default(base_config, dotfiles_dir, tmp_path):
    profile = resolve_profile("default", base_config)
    assert profile.name == "default"
    assert "vimrc" in profile.files


def test_resolve_profile_inherits_parent(base_config, tmp_path):
    profile = resolve_profile("work", base_config)
    assert "vimrc" in profile.files  # inherited from default
    assert ".bashrc_work" in profile.files["bashrc"]


def test_resolve_unknown_profile_raises(base_config):
    with pytest.raises(ValueError, match="not found"):
        resolve_profile("nonexistent", base_config)


def test_sync_creates_symlinks(base_config, dotfiles_dir, tmp_path):
    home = tmp_path / "home"
    profile = resolve_profile("default", base_config)
    logs = []
    actions = sync_profile(profile, backup=False, symlink=True, log=logs.append)
    assert (home / ".vimrc").is_symlink()
    assert (home / ".bashrc").is_symlink()
    assert any("SYMLINK" in a for a in actions)


def test_sync_dry_run_does_not_create_files(base_config, dotfiles_dir, tmp_path):
    home = tmp_path / "home"
    profile = resolve_profile("default", base_config)
    sync_profile(profile, backup=False, symlink=True, dry_run=True)
    assert not (home / ".vimrc").exists()
    assert not (home / ".bashrc").exists()
