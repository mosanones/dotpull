"""Tests for dotpull.cli_lint."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from dotpull.cli_lint import lint_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    (dotfiles / "zshrc").write_text("export EDITOR=vim")

    config = tmp_path / "dotpull.yaml"
    config.write_text(
        f"dotfiles_dir: {dotfiles}\n"
        "profiles:\n"
        "  default:\n"
        "    files:\n"
        "      zshrc: ~/.zshrc\n"
        "    variables:\n"
        "      EDITOR: vim\n"
    )
    return {"config": str(config), "dotfiles": dotfiles}


def test_check_all_profiles_clean(runner, dotpull_env):
    result = runner.invoke(
        lint_group, ["check", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_check_single_profile_clean(runner, dotpull_env):
    result = runner.invoke(
        lint_group,
        ["check", "--config", dotpull_env["config"], "--profile", "default"],
    )
    assert result.exit_code == 0


def test_check_unknown_profile_exits(runner, dotpull_env):
    result = runner.invoke(
        lint_group,
        ["check", "--config", dotpull_env["config"], "--profile", "ghost"],
    )
    assert result.exit_code != 0
    assert "Unknown profile" in result.output


def test_check_missing_source_exits_nonzero(runner, tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config = tmp_path / "dotpull.yaml"
    config.write_text(
        f"dotfiles_dir: {dotfiles}\n"
        "profiles:\n"
        "  default:\n"
        "    files:\n"
        "      ghost.conf: ~/.ghost.conf\n"
    )
    result = runner.invoke(lint_group, ["check", "--config", str(config)])
    assert result.exit_code != 0
    assert "ghost.conf" in result.output


def test_check_strict_exits_on_warning(runner, tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config = tmp_path / "dotpull.yaml"
    # Profile with no files triggers a warning
    config.write_text(
        f"dotfiles_dir: {dotfiles}\n"
        "profiles:\n"
        "  empty_profile:\n"
        "    files: {}\n"
    )
    result = runner.invoke(
        lint_group, ["check", "--config", str(config), "--strict"]
    )
    assert result.exit_code != 0
