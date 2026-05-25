"""Tests for dotpull.cli_archive."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from dotpull.cli_archive import archive_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    (dotfiles / "bashrc").write_text("# bash\n")
    (dotfiles / "zshrc").write_text("# zsh\n")

    config = tmp_path / "dotpull.yaml"
    config.write_text(f"dotfiles_dir: {dotfiles}\nprofiles: {{}}\n")
    return {"config": str(config), "dotfiles": dotfiles}


def test_create_archive_success(runner: CliRunner, dotpull_env: dict):
    result = runner.invoke(
        archive_group, ["create", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "Archive created" in result.output
    assert "SHA-256" in result.output


def test_create_archive_with_label(runner: CliRunner, dotpull_env: dict):
    result = runner.invoke(
        archive_group,
        ["create", "--config", dotpull_env["config"], "--label", "weekly"],
    )
    assert result.exit_code == 0
    assert "weekly" in result.output


def test_list_archives_empty(runner: CliRunner, dotpull_env: dict):
    result = runner.invoke(
        archive_group, ["list", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "No archives found" in result.output


def test_list_archives_shows_entries(runner: CliRunner, dotpull_env: dict):
    runner.invoke(archive_group, ["create", "--config", dotpull_env["config"], "--label", "snap1"])
    runner.invoke(archive_group, ["create", "--config", dotpull_env["config"], "--label", "snap2"])
    result = runner.invoke(
        archive_group, ["list", "--config", dotpull_env["config"]]
    )
    assert result.exit_code == 0
    assert "snap1" in result.output
    assert "snap2" in result.output


def test_restore_archive_success(runner: CliRunner, dotpull_env: dict, tmp_path: Path):
    runner.invoke(archive_group, ["create", "--config", dotpull_env["config"], "--label", "test"])
    archives_dir = dotpull_env["dotfiles"] / ".archives"
    archive_file = next(archives_dir.glob("*.tar.gz"))
    target = tmp_path / "out"
    result = runner.invoke(
        archive_group,
        ["restore", str(archive_file), "--config", dotpull_env["config"], "--target", str(target)],
    )
    assert result.exit_code == 0
    assert "Restored" in result.output


def test_restore_missing_archive_exits_nonzero(runner: CliRunner, dotpull_env: dict, tmp_path: Path):
    result = runner.invoke(
        archive_group,
        ["restore", "/nonexistent/ghost.tar.gz", "--config", dotpull_env["config"]],
    )
    assert result.exit_code != 0
    assert "Error" in result.output
