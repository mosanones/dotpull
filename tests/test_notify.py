"""Tests for dotpull.notify."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from dotpull.notify import (
    NotifyEvent,
    NotifyLevel,
    _notify_desktop,
    _notify_echo,
    notify_link,
    notify_sync,
    send_notification,
)


def test_notify_event_to_dict():
    event = NotifyEvent(
        title="T", message="M", level=NotifyLevel.WARNING, profile="work", tags=["a"]
    )
    d = event.to_dict()
    assert d["title"] == "T"
    assert d["level"] == "warning"
    assert d["profile"] == "work"
    assert d["tags"] == ["a"]


def test_notify_echo_returns_true(capsys):
    event = NotifyEvent(title="Hello", message="World", level=NotifyLevel.INFO)
    result = _notify_echo(event)
    assert result is True
    captured = capsys.readouterr()
    assert "Hello" in captured.out
    assert "World" in captured.out


def test_notify_echo_error_prefix(capsys):
    event = NotifyEvent(title="Err", message="bad", level=NotifyLevel.ERROR)
    _notify_echo(event)
    captured = capsys.readouterr()
    assert "[x]" in captured.out


def test_notify_desktop_returns_false_when_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        event = NotifyEvent(title="T", message="M")
        assert _notify_desktop(event) is False


def test_notify_desktop_returns_true_on_success():
    with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
        event = NotifyEvent(title="T", message="M", level=NotifyLevel.INFO)
        result = _notify_desktop(event)
        assert result is True
        mock_run.assert_called_once()


def test_send_notification_falls_back_to_echo(capsys):
    with patch("dotpull.notify._notify_desktop", return_value=False):
        event = NotifyEvent(title="FB", message="fallback")
        result = send_notification(event, desktop=True, fallback_echo=True)
        assert result is True
        out = capsys.readouterr().out
        assert "FB" in out


def test_send_notification_no_fallback_returns_false():
    with patch("dotpull.notify._notify_desktop", return_value=False):
        event = NotifyEvent(title="X", message="Y")
        result = send_notification(event, desktop=True, fallback_echo=False)
        assert result is False


def test_notify_sync_success(capsys):
    with patch("dotpull.notify._notify_desktop", return_value=False):
        result = notify_sync("home", success=True)
        assert result is True
        out = capsys.readouterr().out
        assert "home" in out
        assert "successfully" in out


def test_notify_sync_failure(capsys):
    with patch("dotpull.notify._notify_desktop", return_value=False):
        result = notify_sync("work", success=False)
        assert result is True
        out = capsys.readouterr().out
        assert "failed" in out


def test_notify_link_success(capsys):
    with patch("dotpull.notify._notify_desktop", return_value=False):
        result = notify_link("dev", success=True)
        assert result is True
        out = capsys.readouterr().out
        assert "dev" in out
