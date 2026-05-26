"""Tests for dotpull.cli_promote."""
from __future__ import annotations

import pytest
import yaml
from click.testing import CliRunner
from pathlib import Path

from dotpull.cli_promote import promote_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config = tmp_path / "dotpull.yaml"
    config.write_text(yaml.dump({"dotfiles_dir": str(dotfiles)}))
    profiles = dotfiles / "profiles.yaml"
    profiles.write_text(yaml.dump({
        "dev": {
            "files": {"bashrc": "~/.bashrc"},
            "variables": {"editor": "nvim"},
        },
        "prod": {
            "files": {},
            "variables": {},
        },
    }))
    return {"config": str(config), "dotfiles": dotfiles, "profiles": profiles}


def test_apply_promote_merges_files(runner, dotpull_env):
    result = runner.invoke(
        promote_group,
        ["apply", "dev", "prod", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    saved = yaml.safe_load(dotpull_env["profiles"].read_text())
    assert "bashrc" in saved["prod"]["files"]


def test_apply_promote_merges_vars(runner, dotpull_env):
    result = runner.invoke(
        promote_group,
        ["apply", "dev", "prod", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    saved = yaml.safe_load(dotpull_env["profiles"].read_text())
    assert saved["prod"]["variables"].get("editor") == "nvim"


def test_apply_promote_unknown_source_exits(runner, dotpull_env):
    result = runner.invoke(
        promote_group,
        ["apply", "ghost", "prod", "--config", dotpull_env["config"]],
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_apply_promote_unknown_target_exits(runner, dotpull_env):
    result = runner.invoke(
        promote_group,
        ["apply", "dev", "nowhere", "--config", dotpull_env["config"]],
    )
    assert result.exit_code != 0


def test_apply_promote_overwrite_flag(runner, dotpull_env):
    # Pre-set a conflicting variable in prod
    profiles = dotpull_env["profiles"]
    data = yaml.safe_load(profiles.read_text())
    data["prod"]["variables"]["editor"] = "vim"
    profiles.write_text(yaml.dump(data))

    result = runner.invoke(
        promote_group,
        ["apply", "dev", "prod", "--overwrite", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    saved = yaml.safe_load(profiles.read_text())
    assert saved["prod"]["variables"]["editor"] == "nvim"
