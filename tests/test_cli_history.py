"""Tests for dotpull.cli_history."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from dotpull.cli_history import history_group
from dotpull.history import make_entry, record_entry, HISTORY_FILE


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config = tmp_path / "dotpull.yaml"
    config.write_text(
        f"dotfiles_dir: {dotfiles}\nprofiles_file: {tmp_path / 'profiles.yaml'}\n"
    )
    (tmp_path / "profiles.yaml").write_text("profiles: {}\n")
    return {"config": str(config), "dotfiles": dotfiles}


def test_show_empty_history(runner, dotpull_env):
    result = runner.invoke(
        history_group, ["show", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "No history" in result.output


def test_show_lists_entries(runner, dotpull_env):
    dotfiles = dotpull_env["dotfiles"]
    record_entry(dotfiles, make_entry("default", "sync", files_affected=[".bashrc"]))
    result = runner.invoke(
        history_group, ["show", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "sync" in result.output
    assert "default" in result.output
    assert ".bashrc" in result.output


def test_show_filters_by_profile(runner, dotpull_env):
    dotfiles = dotpull_env["dotfiles"]
    record_entry(dotfiles, make_entry("default", "sync"))
    record_entry(dotfiles, make_entry("work", "link"))
    result = runner.invoke(
        history_group,
        ["show", "--config", dotpull_env["config"], "--profile", "work"],
    )
    assert result.exit_code == 0
    assert "work" in result.output
    assert "default" not in result.output


def test_show_respects_limit(runner, dotpull_env):
    dotfiles = dotpull_env["dotfiles"]
    for i in range(5):
        record_entry(dotfiles, make_entry("default", "sync", note=f"run-{i}"))
    result = runner.invoke(
        history_group,
        ["show", "--config", dotpull_env["config"], "--limit", "2"],
    )
    assert result.exit_code == 0
    assert result.output.count("sync") == 2


def test_clear_removes_history_file(runner, dotpull_env):
    dotfiles = dotpull_env["dotfiles"]
    record_entry(dotfiles, make_entry("default", "sync"))
    assert (dotfiles / HISTORY_FILE).exists()
    result = runner.invoke(
        history_group,
        ["clear", "--config", dotpull_env["config"], "--yes"],
    )
    assert result.exit_code == 0
    assert not (dotfiles / HISTORY_FILE).exists()
    assert "cleared" in result.output
