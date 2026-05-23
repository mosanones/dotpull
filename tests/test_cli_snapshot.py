"""Tests for dotpull.cli_snapshot CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from dotpull.cli_snapshot import snapshot_group
from dotpull.snapshot import create_snapshot


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def dotpull_env(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    (dotfiles / "bashrc").write_text("# bashrc")
    (dotfiles / "zshrc").write_text("# zshrc")

    config_file = tmp_path / "dotpull.toml"
    config_file.write_text(f'dotfiles_dir = "{dotfiles}"\n')
    return {"config": str(config_file), "dotfiles": dotfiles}


def test_create_snapshot_success(runner, dotpull_env):
    result = runner.invoke(
        snapshot_group, ["create", "--config", dotpull_env["config"], "--label", "ci"]
    )
    assert result.exit_code == 0
    assert "Snapshot created" in result.output
    assert "ci" in result.output


def test_create_snapshot_no_label(runner, dotpull_env):
    result = runner.invoke(
        snapshot_group, ["create", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "Snapshot created" in result.output


def test_list_snapshots_shows_entries(runner, dotpull_env):
    create_snapshot(dotpull_env["dotfiles"], label="alpha")
    create_snapshot(dotpull_env["dotfiles"], label="beta")
    result = runner.invoke(
        snapshot_group, ["list", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output


def test_list_snapshots_empty(runner, dotpull_env):
    result = runner.invoke(
        snapshot_group, ["list", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "No snapshots found" in result.output


def test_restore_snapshot_success(runner, dotpull_env):
    snap = create_snapshot(dotpull_env["dotfiles"], label="restore-test")
    (dotpull_env["dotfiles"] / "bashrc").write_text("# changed")
    result = runner.invoke(
        snapshot_group, ["restore", snap.name, "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "Restored" in result.output


def test_restore_missing_snapshot_exits(runner, dotpull_env):
    result = runner.invoke(
        snapshot_group, ["restore", "ghost_snap", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 1
    assert "Error" in result.output
