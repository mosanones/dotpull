"""Tests for dotpull.cli_remote CLI commands."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dotpull.cli_remote import remote_group
from dotpull.remote import RemoteError, RemoteResult


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def dotpull_env(tmp_path):
    cfg = tmp_path / "dotpull.toml"
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    cfg.write_text(f'dotfiles_dir = "{dotfiles}"\ndefault_profile = "default"\n')
    return {"config": str(cfg), "dotfiles_dir": dotfiles}


def test_push_success(runner, dotpull_env):
    ok = RemoteResult(success=True, message="Pushed successfully", output="")
    with patch("dotpull.cli_remote.remote_push", return_value=ok):
        result = runner.invoke(remote_group, ["push", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "Pushed" in result.output


def test_push_with_message(runner, dotpull_env):
    ok = RemoteResult(success=True, message="Pushed successfully", output="")
    with patch("dotpull.cli_remote.remote_push", return_value=ok) as mock_push:
        runner.invoke(
            remote_group,
            ["push", "--config", dotpull_env["config"], "-m", "my commit"],
        )
    mock_push.assert_called_once()
    assert mock_push.call_args.kwargs["message"] == "my commit"


def test_push_failure_exits_nonzero(runner, dotpull_env):
    fail = RemoteResult(success=False, message="git push failed", errors=["rejected"])
    with patch("dotpull.cli_remote.remote_push", return_value=fail):
        result = runner.invoke(remote_group, ["push", "--config", dotpull_env["config"]])
    assert result.exit_code != 0


def test_push_remote_error_exits(runner, dotpull_env):
    with patch("dotpull.cli_remote.remote_push", side_effect=RemoteError("not a repo")):
        result = runner.invoke(remote_group, ["push", "--config", dotpull_env["config"]])
    assert result.exit_code != 0
    assert "not a repo" in result.output


def test_pull_success(runner, dotpull_env):
    ok = RemoteResult(success=True, message="Pulled successfully", output="Already up to date.")
    with patch("dotpull.cli_remote.remote_pull", return_value=ok):
        result = runner.invoke(remote_group, ["pull", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "Pulled" in result.output


def test_status_shows_output(runner, dotpull_env):
    ok = RemoteResult(success=True, message="Status retrieved", output=" M .vimrc")
    with patch("dotpull.cli_remote.remote_status", return_value=ok):
        result = runner.invoke(remote_group, ["status", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert ".vimrc" in result.output


def test_status_clean_tree_message(runner, dotpull_env):
    ok = RemoteResult(success=True, message="Status retrieved", output="")
    with patch("dotpull.cli_remote.remote_status", return_value=ok):
        result = runner.invoke(remote_group, ["status", "--config", dotpull_env["config"]])
    assert result.exit_code == 0
    assert "clean" in result.output
