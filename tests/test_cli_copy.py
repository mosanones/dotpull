"""Tests for dotpull.cli_copy."""
from __future__ import annotations

import pytest
from pathlib import Path
from click.testing import CliRunner

from dotpull.cli_copy import copy_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config = tmp_path / "dotpull.yaml"
    config.write_text(
        f"dotfiles_dir: {dotfiles}\nprofiles_file: {tmp_path / 'profiles.yaml'}\n"
    )
    profiles = tmp_path / "profiles.yaml"
    profiles.write_text("profiles:\n  default:\n    files: []\n")
    src = tmp_path / "src"
    src.mkdir()
    return {"config": str(config), "dotfiles": dotfiles, "src": src}


def test_add_copies_file(runner, dotpull_env):
    src = dotpull_env["src"] / ".bashrc"
    src.write_text("# bash")

    result = runner.invoke(
        copy_group,
        ["add", str(src), "--dest", ".bashrc", "--config", dotpull_env["config"]],
    )

    assert result.exit_code == 0
    assert (dotpull_env["dotfiles"] / ".bashrc").read_text() == "# bash"


def test_add_dry_run_prints_skipped(runner, dotpull_env):
    src = dotpull_env["src"] / ".zshrc"
    src.write_text("zsh")

    result = runner.invoke(
        copy_group,
        ["add", str(src), "--dest", ".zshrc", "--dry-run", "--config", dotpull_env["config"]],
    )

    assert result.exit_code == 0
    assert "skipped" in result.output
    assert not (dotpull_env["dotfiles"] / ".zshrc").exists()


def test_add_missing_source_exits_nonzero(runner, dotpull_env):
    result = runner.invoke(
        copy_group,
        ["add", "/no/such/file.conf", "--config", dotpull_env["config"]],
    )
    # click's exists=True check fires before our code
    assert result.exit_code != 0


def test_add_overwrite_flag(runner, dotpull_env):
    dest_file = dotpull_env["dotfiles"] / ".tmux.conf"
    dest_file.write_text("old")
    src = dotpull_env["src"] / ".tmux.conf"
    src.write_text("new")

    result = runner.invoke(
        copy_group,
        [
            "add", str(src),
            "--dest", ".tmux.conf",
            "--overwrite",
            "--config", dotpull_env["config"],
        ],
    )

    assert result.exit_code == 0
    assert dest_file.read_text() == "new"
    assert "backup" in result.output


def test_add_no_overwrite_exits_nonzero(runner, dotpull_env):
    dest_file = dotpull_env["dotfiles"] / ".vimrc"
    dest_file.write_text("old")
    src = dotpull_env["src"] / ".vimrc"
    src.write_text("new")

    result = runner.invoke(
        copy_group,
        ["add", str(src), "--dest", ".vimrc", "--config", dotpull_env["config"]],
    )

    assert result.exit_code != 0
    assert dest_file.read_text() == "old"
