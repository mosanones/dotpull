"""Tests for dotpull.cli_tag."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from dotpull.cli_tag import tag_group
from dotpull.tag import load_tag_store


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config = tmp_path / "dotpull.yaml"
    config.write_text(
        f"dotfiles_dir: {dotfiles}\ndefault_profile: base\nprofiles: {{}}\n"
    )
    return {"config": str(config), "dotfiles_dir": dotfiles}


def test_add_tag_success(runner, dotpull_env):
    result = runner.invoke(
        tag_group, ["add", "work", "laptop", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "Tagged 'work' with 'laptop'" in result.output


def test_add_tag_persists(runner, dotpull_env):
    runner.invoke(tag_group, ["add", "work", "laptop", "--config", dotpull_env["config"]])
    store = load_tag_store(dotpull_env["dotfiles_dir"])
    assert "laptop" in store.tags_for("work")


def test_remove_tag_success(runner, dotpull_env):
    runner.invoke(tag_group, ["add", "work", "laptop", "--config", dotpull_env["config"]])
    result = runner.invoke(
        tag_group, ["remove", "work", "laptop", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "Removed tag" in result.output


def test_remove_missing_tag_exits_nonzero(runner, dotpull_env):
    result = runner.invoke(
        tag_group, ["remove", "work", "ghost", "--config", dotpull_env["config"]]
    )
    assert result.exit_code != 0


def test_list_tags_for_profile(runner, dotpull_env):
    runner.invoke(tag_group, ["add", "work", "laptop", "--config", dotpull_env["config"]])
    runner.invoke(tag_group, ["add", "work", "office", "--config", dotpull_env["config"]])
    result = runner.invoke(
        tag_group, ["list", "--profile", "work", "--config", dotpull_env["config"]]
    )
    assert "laptop" in result.output
    assert "office" in result.output


def test_list_profiles_for_tag(runner, dotpull_env):
    runner.invoke(tag_group, ["add", "work", "laptop", "--config", dotpull_env["config"]])
    runner.invoke(tag_group, ["add", "home", "laptop", "--config", dotpull_env["config"]])
    result = runner.invoke(
        tag_group, ["list", "--tag", "laptop", "--config", dotpull_env["config"]]
    )
    assert "work" in result.output
    assert "home" in result.output


def test_list_all_tags_no_filter(runner, dotpull_env):
    runner.invoke(tag_group, ["add", "work", "laptop", "--config", dotpull_env["config"]])
    runner.invoke(tag_group, ["add", "server", "remote", "--config", dotpull_env["config"]])
    result = runner.invoke(tag_group, ["list", "--config", dotpull_env["config"]])
    assert "laptop" in result.output
    assert "remote" in result.output
