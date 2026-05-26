"""Tests for dotpull.cli_notify CLI commands."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dotpull.cli_notify import notify_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_send_info_notification(runner):
    with patch("dotpull.cli_notify.send_notification", return_value=True) as mock_send:
        result = runner.invoke(notify_group, ["send", "Title", "Body"])
        assert result.exit_code == 0
        assert "sent" in result.output
        call_event = mock_send.call_args[0][0]
        assert call_event.title == "Title"
        assert call_event.message == "Body"
        assert call_event.level.value == "info"


def test_send_error_level(runner):
    with patch("dotpull.cli_notify.send_notification", return_value=True) as mock_send:
        result = runner.invoke(
            notify_group, ["send", "Err", "bad thing", "--level", "error"]
        )
        assert result.exit_code == 0
        assert mock_send.call_args[0][0].level.value == "error"


def test_send_with_profile(runner):
    with patch("dotpull.cli_notify.send_notification", return_value=True) as mock_send:
        result = runner.invoke(
            notify_group, ["send", "T", "M", "--profile", "work"]
        )
        assert result.exit_code == 0
        assert mock_send.call_args[0][0].profile == "work"


def test_send_failure_exits_nonzero(runner):
    with patch("dotpull.cli_notify.send_notification", return_value=False):
        result = runner.invoke(notify_group, ["send", "T", "M"])
        assert result.exit_code != 0


def test_test_command_success(runner):
    with patch("dotpull.cli_notify.send_notification", return_value=True):
        result = runner.invoke(notify_group, ["test"])
        assert result.exit_code == 0
        assert "successfully" in result.output


def test_test_command_failure_exits_nonzero(runner):
    with patch("dotpull.cli_notify.send_notification", return_value=False):
        result = runner.invoke(notify_group, ["test"])
        assert result.exit_code != 0
