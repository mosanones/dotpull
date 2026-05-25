"""Tests for dotpull.env."""

from __future__ import annotations

import os

import pytest

from dotpull.env import (
    EnvError,
    EnvSnapshot,
    capture_env,
    inject_env_into_vars,
    required_env,
)


# ---------------------------------------------------------------------------
# capture_env
# ---------------------------------------------------------------------------

def test_capture_env_no_prefix_returns_all(monkeypatch):
    monkeypatch.setenv("DOTPULL_TEST_VAR", "hello")
    snapshot = capture_env()
    assert "DOTPULL_TEST_VAR" in snapshot.variables


def test_capture_env_with_prefix_filters(monkeypatch):
    monkeypatch.setenv("DOTPULL_KEEP", "yes")
    monkeypatch.setenv("OTHER_VAR", "no")
    snapshot = capture_env(prefixes=["DOTPULL_"])
    assert "DOTPULL_KEEP" in snapshot.variables
    assert "OTHER_VAR" not in snapshot.variables


def test_capture_env_multiple_prefixes(monkeypatch):
    monkeypatch.setenv("HOME_DIR", "/home/user")
    monkeypatch.setenv("XDG_DATA", "/usr/share")
    monkeypatch.setenv("IGNORE_THIS", "nope")
    snapshot = capture_env(prefixes=["HOME_", "XDG_"])
    assert "HOME_DIR" in snapshot.variables
    assert "XDG_DATA" in snapshot.variables
    assert "IGNORE_THIS" not in snapshot.variables


def test_capture_env_no_matches_returns_empty(monkeypatch):
    snapshot = capture_env(prefixes=["ZZZNOMATCH_"])
    assert snapshot.variables == {}


# ---------------------------------------------------------------------------
# inject_env_into_vars
# ---------------------------------------------------------------------------

def test_inject_overwrites_by_default():
    base = {"FOO": "original", "BAR": "keep"}
    snap = EnvSnapshot(variables={"FOO": "overridden"})
    result = inject_env_into_vars(base, snap)
    assert result["FOO"] == "overridden"
    assert result["BAR"] == "keep"


def test_inject_no_overwrite_preserves_base():
    base = {"FOO": "original"}
    snap = EnvSnapshot(variables={"FOO": "env_value", "NEW": "added"})
    result = inject_env_into_vars(base, snap, overwrite=False)
    assert result["FOO"] == "original"
    assert result["NEW"] == "added"


def test_inject_does_not_mutate_base():
    base = {"A": "1"}
    snap = EnvSnapshot(variables={"B": "2"})
    inject_env_into_vars(base, snap)
    assert "B" not in base


# ---------------------------------------------------------------------------
# required_env
# ---------------------------------------------------------------------------

def test_required_env_returns_values(monkeypatch):
    monkeypatch.setenv("DOTPULL_REQ_A", "alpha")
    monkeypatch.setenv("DOTPULL_REQ_B", "beta")
    result = required_env(["DOTPULL_REQ_A", "DOTPULL_REQ_B"])
    assert result == {"DOTPULL_REQ_A": "alpha", "DOTPULL_REQ_B": "beta"}


def test_required_env_raises_on_missing(monkeypatch):
    monkeypatch.delenv("DOTPULL_MISSING_VAR", raising=False)
    with pytest.raises(EnvError, match="DOTPULL_MISSING_VAR"):
        required_env(["DOTPULL_MISSING_VAR"])


def test_required_env_lists_all_missing(monkeypatch):
    monkeypatch.delenv("DOTPULL_MISS1", raising=False)
    monkeypatch.delenv("DOTPULL_MISS2", raising=False)
    with pytest.raises(EnvError) as exc_info:
        required_env(["DOTPULL_MISS1", "DOTPULL_MISS2"])
    assert "DOTPULL_MISS1" in str(exc_info.value)
    assert "DOTPULL_MISS2" in str(exc_info.value)
