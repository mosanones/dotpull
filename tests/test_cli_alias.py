"""Integration tests for the alias CLI commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from dotpull.cli_alias import alias_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    cfg = tmp_path / "dotpull.yaml"
    cfg.write_text(f"dotfiles_dir: {dotfiles}\n")
    return {"config": str(cfg), "dotfiles": dotfiles}


def test_set_alias_success(runner, dotpull_env):
    result = runner.invoke(
        alias_group,
        ["set", "work", "work-linux", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "work" in result.output
    assert "work-linux" in result.output


def test_set_alias_persists(runner, dotpull_env):
    runner.invoke(
        alias_group,
        ["set", "dev", "dev-profile", "--config", dotpull_env["config"]],
    )
    result = runner.invoke(
        alias_group, ["list", "--config", dotpull_env["config"]]
    )
    assert "dev" in result.output
    assert "dev-profile" in result.output


def test_remove_alias_success(runner, dotpull_env):
    runner.invoke(
        alias_group,
        ["set", "tmp", "tmp-profile", "--config", dotpull_env["config"]],
    )
    result = runner.invoke(
        alias_group,
        ["remove", "tmp", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_missing_alias(runner, dotpull_env):
    result = runner.invoke(
        alias_group,
        ["remove", "ghost", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "not found" in result.output


def test_list_empty(runner, dotpull_env):
    result = runner.invoke(
        alias_group, ["list", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "No aliases" in result.output


def test_resolve_known_alias(runner, dotpull_env):
    runner.invoke(
        alias_group,
        ["set", "w", "work-linux", "--config", dotpull_env["config"]],
    )
    result = runner.invoke(
        alias_group,
        ["resolve", "w", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "work-linux" in result.output


def test_resolve_unknown_returns_name(runner, dotpull_env):
    result = runner.invoke(
        alias_group,
        ["resolve", "mystery", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "mystery" in result.output
