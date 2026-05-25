"""Tests for dotpull.cli_search CLI commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from dotpull.cli_search import search_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    (dotfiles / "bashrc").write_text("# bash")
    (dotfiles / "vimrc").write_text("# vim")
    (dotfiles / "app.toml").write_text("[settings]")

    config = tmp_path / "dotpull.yaml"
    config.write_text(f"dotfiles_dir: {dotfiles}\n")

    profiles = dotfiles / "profiles.yaml"
    profiles.write_text(
        "base:\n"
        "  files:\n"
        "    bashrc: ~/.bashrc\n"
        "    vimrc: ~/.vimrc\n"
        "    app.toml: ~/.config/app.toml\n"
        "  variables:\n"
        "    editor: vim\n"
        "work:\n"
        "  files:\n"
        "    gitconfig: ~/.gitconfig\n"
        "  variables:\n"
        "    git_email: work@example.com\n"
    )
    return {"config": str(config)}


def test_query_finds_file_match(runner, dotpull_env):
    result = runner.invoke(
        search_group, ["query", "vim", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "base" in result.output
    assert "vimrc" in result.output


def test_query_finds_variable_match(runner, dotpull_env):
    result = runner.invoke(
        search_group, ["query", "email", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "work" in result.output
    assert "git_email" in result.output


def test_query_no_match_exits_zero(runner, dotpull_env):
    result = runner.invoke(
        search_group, ["query", "zzznomatch", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "No matches" in result.output


def test_ext_finds_toml_files(runner, dotpull_env):
    result = runner.invoke(
        search_group, ["ext", "toml", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "base" in result.output
    assert "app.toml" in result.output


def test_ext_no_match_exits_zero(runner, dotpull_env):
    result = runner.invoke(
        search_group, ["ext", "rs", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "No profiles" in result.output
