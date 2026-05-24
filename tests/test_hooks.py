"""Tests for dotpull.hooks module."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from dotpull.hooks import (
    HookError,
    HookResult,
    collect_hooks,
    run_hook,
    run_hooks,
)


def test_run_hook_success():
    result = run_hook(f"{sys.executable} -c 'print(\"hello\")'")  
    assert result.success
    assert result.returncode == 0
    assert result.stdout == "hello"


def test_run_hook_failure():
    result = run_hook(f"{sys.executable} -c 'import sys; sys.exit(2)'")
    assert not result.success
    assert result.returncode == 2


def test_run_hook_timeout_raises():
    with pytest.raises(HookError, match="timed out"):
        run_hook(f"{sys.executable} -c 'import time; time.sleep(10)'", timeout=1)


def test_run_hooks_all_succeed():
    cmds = [
        f"{sys.executable} -c 'print(1)'",
        f"{sys.executable} -c 'print(2)'",
    ]
    results = run_hooks(cmds)
    assert len(results) == 2
    assert all(r.success for r in results)


def test_run_hooks_stop_on_failure():
    cmds = [
        f"{sys.executable} -c 'import sys; sys.exit(1)'",
        f"{sys.executable} -c 'print(\"should not run\")'",
    ]
    with pytest.raises(HookError, match="Hook failed"):
        run_hooks(cmds, stop_on_failure=True)


def test_run_hooks_continue_on_failure():
    cmds = [
        f"{sys.executable} -c 'import sys; sys.exit(1)'",
        f"{sys.executable} -c 'print(\"ran\")'",
    ]
    results = run_hooks(cmds, stop_on_failure=False)
    assert len(results) == 2
    assert not results[0].success
    assert results[1].success


def test_collect_hooks_returns_stage_commands():
    profile = {"hooks": {"pre_sync": ["echo before"], "post_sync": ["echo after"]}}
    assert collect_hooks(profile, "pre_sync") == ["echo before"]
    assert collect_hooks(profile, "post_sync") == ["echo after"]


def test_collect_hooks_missing_stage_returns_empty():
    profile = {"hooks": {}}
    assert collect_hooks(profile, "pre_sync") == []


def test_collect_hooks_no_hooks_key_returns_empty():
    profile = {}
    assert collect_hooks(profile, "post_sync") == []


def test_collect_hooks_invalid_hooks_type_raises():
    profile = {"hooks": "not-a-dict"}
    with pytest.raises(HookError, match="mapping"):
        collect_hooks(profile, "pre_sync")
