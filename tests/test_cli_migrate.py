"""Tests for dotpull.cli_migrate."""
from __future__ import annotations

import yaml
import pytest
from pathlib import Path
from click.testing import CliRunner

from dotpull.cli_migrate import migrate_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()

    config = tmp_path / "dotpull.yaml"
    config.write_text(yaml.safe_dump({"dotfiles_dir": str(dotfiles)}))

    profiles_data = {
        "profiles": {
            "base": {"files": [".bashrc"]},
            "work": {"extends": "base", "files": [".vimrc"]},
        }
    }
    (dotfiles / "profiles.yaml").write_text(yaml.safe_dump(profiles_data))

    return {"config": str(config), "dotfiles": dotfiles}


def _read_profiles(env: dict) -> dict:
    return yaml.safe_load((env["dotfiles"] / "profiles.yaml").read_text())


def test_rename_success(runner: CliRunner, dotpull_env: dict) -> None:
    result = runner.invoke(
        migrate_group, ["rename", "base", "common", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0, result.output
    data = _read_profiles(dotpull_env)
    assert "common" in data["profiles"]
    assert "base" not in data["profiles"]


def test_rename_updates_extends(runner: CliRunner, dotpull_env: dict) -> None:
    runner.invoke(
        migrate_group, ["rename", "base", "common", "--config", dotpull_env["config"]]
    )
    data = _read_profiles(dotpull_env)
    assert data["profiles"]["work"]["extends"] == "common"


def test_rename_conflict_exits_nonzero(runner: CliRunner, dotpull_env: dict) -> None:
    result = runner.invoke(
        migrate_group, ["rename", "base", "work", "--config", dotpull_env["config"]]
    )
    assert result.exit_code != 0


def test_rename_overwrite_flag(runner: CliRunner, dotpull_env: dict) -> None:
    result = runner.invoke(
        migrate_group,
        ["rename", "base", "work", "--overwrite", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0, result.output


def test_copy_success(runner: CliRunner, dotpull_env: dict) -> None:
    result = runner.invoke(
        migrate_group, ["copy", "base", "base_copy", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0, result.output
    data = _read_profiles(dotpull_env)
    assert "base" in data["profiles"]
    assert "base_copy" in data["profiles"]


def test_copy_unknown_profile_exits(runner: CliRunner, dotpull_env: dict) -> None:
    result = runner.invoke(
        migrate_group, ["copy", "ghost", "new", "--config", dotpull_env["config"]]
    )
    assert result.exit_code != 0
