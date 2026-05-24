"""Tests for dotpull.remote module."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from dotpull.remote import (
    RemoteError,
    RemoteResult,
    is_git_repo,
    remote_pull,
    remote_push,
    remote_status,
)


def _mock_run(returncode: int, stdout: str = "", stderr: str = ""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


@pytest.fixture
def repo_dir(tmp_path):
    return tmp_path


def test_is_git_repo_returns_true_when_git_present(repo_dir):
    with patch("subprocess.run", return_value=_mock_run(0, ".git")):
        assert is_git_repo(repo_dir) is True


def test_is_git_repo_returns_false_when_not_git(repo_dir):
    with patch("subprocess.run", return_value=_mock_run(128)):
        assert is_git_repo(repo_dir) is False


def test_remote_push_success(repo_dir):
    responses = [
        _mock_run(0),        # git rev-parse
        _mock_run(0),        # git add
        _mock_run(0, "[main abc1234] dotpull: sync dotfiles"),  # git commit
        _mock_run(0, "Everything up-to-date"),  # git push
    ]
    with patch("subprocess.run", side_effect=responses):
        result = remote_push(repo_dir)
    assert result.success is True
    assert "Pushed" in result.message


def test_remote_push_uses_custom_message(repo_dir):
    responses = [
        _mock_run(0),
        _mock_run(0),
        _mock_run(0, "[main abc] custom msg"),
        _mock_run(0, ""),
    ]
    with patch("subprocess.run", side_effect=responses) as mock_sub:
        remote_push(repo_dir, message="custom msg")
    commit_call = mock_sub.call_args_list[2]
    assert "custom msg" in commit_call.args[0]


def test_remote_push_fails_when_not_git(repo_dir):
    with patch("subprocess.run", return_value=_mock_run(128)):
        with pytest.raises(RemoteError):
            remote_push(repo_dir)


def test_remote_push_returns_failure_on_push_error(repo_dir):
    responses = [
        _mock_run(0),
        _mock_run(0),
        _mock_run(0, "[main abc] msg"),
        _mock_run(1, stderr="rejected"),
    ]
    with patch("subprocess.run", side_effect=responses):
        result = remote_push(repo_dir)
    assert result.success is False
    assert "rejected" in result.errors[0]


def test_remote_pull_success(repo_dir):
    responses = [_mock_run(0), _mock_run(0, "Already up to date.")]
    with patch("subprocess.run", side_effect=responses):
        result = remote_pull(repo_dir)
    assert result.success is True


def test_remote_pull_fails_when_not_git(repo_dir):
    with patch("subprocess.run", return_value=_mock_run(128)):
        with pytest.raises(RemoteError):
            remote_pull(repo_dir)


def test_remote_status_returns_output(repo_dir):
    responses = [_mock_run(0), _mock_run(0, " M .bashrc")]
    with patch("subprocess.run", side_effect=responses):
        result = remote_status(repo_dir)
    assert result.success is True
    assert ".bashrc" in result.output
