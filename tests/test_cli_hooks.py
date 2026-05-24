"""Tests for dotpull.cli_hooks commands."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from dotpull.cli_hooks import hooks_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config = tmp_path / "dotpull.yaml"
    config.write_text(
        f"dotfiles_dir: {dotfiles}\n"
        "default_profile: default\n"
        "profiles:\n"
        "  default:\n"
        "    files: []\n"
        f"    hooks:\n"
        f"      pre_sync:\n"
        f"        - {sys.executable} -c 'print(\"pre\")' \n"
        f"      post_sync:\n"
        f"        - {sys.executable} -c 'print(\"post\")' \n"
        "  empty:\n"
        "    files: []\n"
    )
    return {"config": str(config), "dotfiles": dotfiles}


def test_run_pre_sync_success(runner, dotpull_env):
    result = runner.invoke(
        hooks_group, ["run", "pre_sync", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_run_post_sync_success(runner, dotpull_env):
    result = runner.invoke(
        hooks_group, ["run", "post_sync", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_run_no_hooks_defined(runner, dotpull_env):
    result = runner.invoke(
        hooks_group,
        ["run", "pre_sync", "--profile", "empty", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "No pre_sync hooks" in result.output


def test_run_unknown_profile_exits(runner, dotpull_env):
    result = runner.invoke(
        hooks_group,
        ["run", "pre_sync", "--profile", "ghost", "--config", dotpull_env["config"]],
    )
    assert result.exit_code != 0
    assert "Unknown profile" in result.output


def test_list_shows_hooks(runner, dotpull_env):
    result = runner.invoke(
        hooks_group, ["list", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "pre_sync" in result.output
    assert "post_sync" in result.output


def test_list_empty_profile(runner, dotpull_env):
    result = runner.invoke(
        hooks_group,
        ["list", "--profile", "empty", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "(none)" in result.output
