"""Tests for dotpull.scaffold."""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from dotpull.scaffold import ScaffoldError, scaffold_profile


@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    profiles = {"base": {"files": [], "variables": {}, "extends": None}}
    (d / "profiles.yaml").write_text(yaml.dump(profiles))
    return d


def test_scaffold_adds_profile_to_yaml(dotfiles_dir):
    scaffold_profile(dotfiles_dir, "work")
    data = yaml.safe_load((dotfiles_dir / "profiles.yaml").read_text())
    assert "work" in data


def test_scaffold_creates_sample_files(dotfiles_dir):
    result = scaffold_profile(dotfiles_dir, "work", sample_files=["home/.vimrc"])
    stub = dotfiles_dir / "home" / ".vimrc"
    assert stub.exists()
    assert stub in result.created_files


def test_scaffold_skips_existing_sample_file(dotfiles_dir):
    existing = dotfiles_dir / "home" / ".vimrc"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("already here")
    result = scaffold_profile(dotfiles_dir, "work", sample_files=["home/.vimrc"])
    assert existing in result.skipped_files
    assert existing not in result.created_files
    assert existing.read_text() == "already here"


def test_scaffold_raises_if_profile_exists(dotfiles_dir):
    with pytest.raises(ScaffoldError, match="already exists"):
        scaffold_profile(dotfiles_dir, "base")


def test_scaffold_raises_if_no_profiles_yaml(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ScaffoldError, match="profiles.yaml not found"):
        scaffold_profile(empty, "new")


def test_scaffold_dry_run_does_not_write(dotfiles_dir):
    result = scaffold_profile(
        dotfiles_dir, "preview", sample_files=["home/.bashrc"], dry_run=True
    )
    data = yaml.safe_load((dotfiles_dir / "profiles.yaml").read_text())
    assert "preview" not in data
    assert not (dotfiles_dir / "home" / ".bashrc").exists()
    assert result.dry_run is True


def test_summary_mentions_profile_name(dotfiles_dir):
    result = scaffold_profile(dotfiles_dir, "laptop", sample_files=["home/.tmux.conf"])
    summary = result.summary()
    assert "laptop" in summary
    assert ".tmux.conf" in summary


def test_scaffold_empty_sample_files_still_creates_profile(dotfiles_dir):
    scaffold_profile(dotfiles_dir, "minimal", sample_files=[])
    data = yaml.safe_load((dotfiles_dir / "profiles.yaml").read_text())
    assert "minimal" in data
    assert data["minimal"]["files"] == []
