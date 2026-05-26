"""Tests for dotpull.cli_group."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from dotpull.cli_group import group_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def dotpull_env(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    cfg = tmp_path / "dotpull.yaml"
    cfg.write_text(yaml.dump({"dotfiles_dir": str(dotfiles), "profiles_file": "profiles.yaml"}))
    return {"config": str(cfg), "dotfiles": dotfiles}


def _read_groups(dotpull_env):
    groups_file = dotpull_env["dotfiles"] / ".dotpull" / "groups.yaml"
    if not groups_file.exists():
        return {}
    return yaml.safe_load(groups_file.read_text()) or {}


def test_add_group_success(runner, dotpull_env):
    result = runner.invoke(group_group, ["add", "work", "base", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "Added 'base' to group 'work'" in result.output


def test_add_group_persists(runner, dotpull_env):
    runner.invoke(group_group, ["add", "work", "base", "--config", dotpull_env["config"]])
    runner.invoke(group_group, ["add", "work", "dev", "--config", dotpull_env["config"]])
    data = _read_groups(dotpull_env)
    assert "base" in data["work"]
    assert "dev" in data["work"]


def test_remove_profile_success(runner, dotpull_env):
    runner.invoke(group_group, ["add", "work", "base", "--config", dotpull_env["config"]])
    result = runner.invoke(group_group, ["remove", "work", "base", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_nonexistent_profile_message(runner, dotpull_env):
    runner.invoke(group_group, ["add", "work", "base", "--config", dotpull_env["config"]])
    result = runner.invoke(group_group, ["remove", "work", "ghost", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "was not in group" in result.output


def test_list_groups(runner, dotpull_env):
    runner.invoke(group_group, ["add", "work", "base", "--config", dotpull_env["config"]])
    runner.invoke(group_group, ["add", "personal", "home", "--config", dotpull_env["config"]])
    result = runner.invoke(group_group, ["list", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "work" in result.output
    assert "personal" in result.output


def test_list_empty_groups(runner, dotpull_env):
    result = runner.invoke(group_group, ["list", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "No groups defined" in result.output


def test_delete_group_success(runner, dotpull_env):
    runner.invoke(group_group, ["add", "work", "base", "--config", dotpull_env["config"]])
    result = runner.invoke(group_group, ["delete", "work", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "Deleted group 'work'" in result.output


def test_delete_missing_group_exits_nonzero(runner, dotpull_env):
    result = runner.invoke(group_group, ["delete", "ghost", "--config", dotpull_env["config"]])
    assert result.exit_code != 0
