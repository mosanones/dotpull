"""Tests for dotpull.watch module."""

import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from dotpull.watch import watch_profile, WatchError, _get_mtimes


@pytest.fixture
def watched_dir(tmp_path):
    (tmp_path / "bashrc").write_text("# bashrc")
    (tmp_path / "vimrc").write_text("# vimrc")
    return tmp_path


def test_get_mtimes_returns_existing_files(watched_dir):
    mtimes = _get_mtimes(watched_dir, ["bashrc", "vimrc"])
    assert len(mtimes) == 2
    assert all(isinstance(v, float) for v in mtimes.values())


def test_get_mtimes_skips_missing_files(watched_dir):
    mtimes = _get_mtimes(watched_dir, ["bashrc", "nonexistent"])
    assert len(mtimes) == 1


def test_watch_raises_on_missing_dir(tmp_path):
    with pytest.raises(WatchError, match="not found"):
        watch_profile(tmp_path / "no_such_dir", [], lambda c: None, stop_after=0)


def test_watch_calls_on_change_when_file_modified(watched_dir):
    callback = MagicMock()

    bashrc = watched_dir / "bashrc"

    def mutate_and_stop():
        time.sleep(0.05)
        bashrc.write_text("# modified")

    import threading
    t = threading.Thread(target=mutate_and_stop)
    t.start()

    watch_profile(
        watched_dir,
        ["bashrc"],
        callback,
        interval=0.02,
        stop_after=10,
    )
    t.join()

    assert callback.called
    changed_files = callback.call_args[0][0]
    assert "bashrc" in changed_files


def test_watch_no_change_callback_not_called(watched_dir):
    callback = MagicMock()
    watch_profile(
        watched_dir,
        ["bashrc", "vimrc"],
        callback,
        interval=0.01,
        stop_after=3,
    )
    callback.assert_not_called()
