"""Tests for dotpull.migrate."""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from dotpull.migrate import MigrateError, copy_profile, rename_profile


@pytest.fixture()
def profiles_file(tmp_path: Path) -> Path:
    data = {
        "profiles": {
            "base": {"files": [".bashrc"]},
            "work": {"extends": "base", "files": [".vimrc"]},
        }
    }
    p = tmp_path / "profiles.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def _read(p: Path) -> dict:
    return yaml.safe_load(p.read_text())


# --- rename_profile ---

def test_rename_profile_renames_key(profiles_file: Path) -> None:
    rename_profile(profiles_file, "base", "common")
    data = _read(profiles_file)
    assert "common" in data["profiles"]
    assert "base" not in data["profiles"]


def test_rename_profile_updates_extends_references(profiles_file: Path) -> None:
    rename_profile(profiles_file, "base", "common")
    data = _read(profiles_file)
    assert data["profiles"]["work"]["extends"] == "common"


def test_rename_profile_missing_source_raises(profiles_file: Path) -> None:
    with pytest.raises(MigrateError, match="does not exist"):
        rename_profile(profiles_file, "ghost", "new")


def test_rename_profile_destination_exists_raises(profiles_file: Path) -> None:
    with pytest.raises(MigrateError, match="already exists"):
        rename_profile(profiles_file, "base", "work")


def test_rename_profile_destination_exists_overwrite(profiles_file: Path) -> None:
    rename_profile(profiles_file, "base", "work", overwrite=True)
    data = _read(profiles_file)
    assert "base" not in data["profiles"]
    assert data["profiles"]["work"]["files"] == [".bashrc"]


# --- copy_profile ---

def test_copy_profile_keeps_source(profiles_file: Path) -> None:
    copy_profile(profiles_file, "base", "base_copy")
    data = _read(profiles_file)
    assert "base" in data["profiles"]
    assert "base_copy" in data["profiles"]


def test_copy_profile_deep_copies_content(profiles_file: Path) -> None:
    copy_profile(profiles_file, "base", "base_copy")
    data = _read(profiles_file)
    assert data["profiles"]["base_copy"]["files"] == [".bashrc"]


def test_copy_profile_missing_source_raises(profiles_file: Path) -> None:
    with pytest.raises(MigrateError, match="does not exist"):
        copy_profile(profiles_file, "ghost", "new")


def test_copy_profile_destination_exists_raises(profiles_file: Path) -> None:
    with pytest.raises(MigrateError, match="already exists"):
        copy_profile(profiles_file, "base", "work")


def test_copy_profile_missing_profiles_file_raises(tmp_path: Path) -> None:
    with pytest.raises(MigrateError, match="not found"):
        copy_profile(tmp_path / "missing.yaml", "base", "copy")
