"""Tests for dotpull.cli_preset CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
import yaml

from dotpull.cli_preset import preset_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def dotpull_env(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config = tmp_path / "dotpull.yaml"
    config.write_text(yaml.dump({"dotfiles_dir": str(dotfiles), "profiles_file": "profiles.yaml"}))
    return {"config": str(config), "dotfiles": dotfiles}


def test_add_preset_success(runner, dotpull_env):
    result = runner.invoke(
        preset_group,
        ["add", "work", "--var", "EDITOR=vim", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "work" in result.output
    assert "1 variable" in result.output


def test_add_preset_with_description(runner, dotpull_env):
    result = runner.invoke(
        preset_group,
        ["add", "home", "--var", "SHELL=zsh", "--description", "Home machine", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    presets_file = dotpull_env["dotfiles"] / ".dotpull" / "presets.yaml"
    data = yaml.safe_load(presets_file.read_text())
    assert data["home"]["description"] == "Home machine"


def test_add_preset_bad_var_format(runner, dotpull_env):
    result = runner.invoke(
        preset_group,
        ["add", "bad", "--var", "NOEQUALS", "--config", dotpull_env["config"]],
    )
    assert result.exit_code != 0


def test_list_presets_empty(runner, dotpull_env):
    result = runner.invoke(preset_group, ["list", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "No presets" in result.output


def test_list_presets_shows_entries(runner, dotpull_env):
    runner.invoke(preset_group, ["add", "work", "--var", "EDITOR=vim", "--config", dotpull_env["config"]])
    result = runner.invoke(preset_group, ["list", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "work" in result.output
    assert "EDITOR=vim" in result.output


def test_remove_preset_success(runner, dotpull_env):
    runner.invoke(preset_group, ["add", "temp", "--var", "X=1", "--config", dotpull_env["config"]])
    result = runner.invoke(preset_group, ["remove", "temp", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_preset_missing_exits_nonzero(runner, dotpull_env):
    result = runner.invoke(preset_group, ["remove", "ghost", "--config", dotpull_env["config"]])
    assert result.exit_code != 0
    assert "Error" in result.output
