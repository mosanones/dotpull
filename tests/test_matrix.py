"""Tests for dotpull.matrix."""

from __future__ import annotations

import pytest

from dotpull.matrix import MatrixRow, MatrixReport, build_matrix


# ---------------------------------------------------------------------------
# Minimal fake Profile / resolve stubs
# ---------------------------------------------------------------------------

class _FakeProfile:
    def __init__(self, name, variables=None, extends=None):
        self.name = name
        self._variables = variables or {}
        self.extends = extends

    def variables(self):
        return self._variables


# We patch resolve_variables so tests don't depend on its internals.
def _fake_resolve(profile_name, profiles, config_vars, env_overrides):
    from dotpull.resolve import ResolvedVars
    merged = {**config_vars, **profiles[profile_name].variables(), **env_overrides}
    return ResolvedVars(merged)


@pytest.fixture()
def profiles():
    return {
        "base": _FakeProfile("base", {"EDITOR": "vim", "SHELL": "bash"}),
    }


@pytest.fixture()
def environments():
    return {
        "work": {"EDITOR": "code"},
        "home": {"EDITOR": "nvim"},
        "server": {},
    }


# ---------------------------------------------------------------------------
# MatrixRow tests
# ---------------------------------------------------------------------------

def test_matrix_row_get_existing_key():
    row = MatrixRow(profile="base", environment="work", variables={"EDITOR": "code"})
    assert row.get("EDITOR") == "code"


def test_matrix_row_get_missing_key_returns_none():
    row = MatrixRow(profile="base", environment="work", variables={})
    assert row.get("MISSING") is None


# ---------------------------------------------------------------------------
# MatrixReport tests
# ---------------------------------------------------------------------------

def test_report_healthy_when_all_same():
    rows = [
        MatrixRow("base", "work", {"EDITOR": "vim"}),
        MatrixRow("base", "home", {"EDITOR": "vim"}),
    ]
    report = MatrixReport(rows=rows, keys=["EDITOR"])
    assert report.healthy() is True


def test_report_not_healthy_when_values_differ():
    rows = [
        MatrixRow("base", "work", {"EDITOR": "code"}),
        MatrixRow("base", "home", {"EDITOR": "nvim"}),
    ]
    report = MatrixReport(rows=rows, keys=["EDITOR"])
    assert report.healthy() is False


def test_differing_keys_returns_correct_keys():
    rows = [
        MatrixRow("base", "work", {"EDITOR": "code", "SHELL": "bash"}),
        MatrixRow("base", "home", {"EDITOR": "nvim", "SHELL": "bash"}),
    ]
    report = MatrixReport(rows=rows, keys=["EDITOR", "SHELL"])
    assert report.differing_keys() == ["EDITOR"]


def test_summary_all_agree():
    rows = [MatrixRow("base", "work", {"EDITOR": "vim"})]
    report = MatrixReport(rows=rows, keys=["EDITOR"])
    assert "agree" in report.summary()


def test_summary_with_differences():
    rows = [
        MatrixRow("base", "work", {"EDITOR": "code"}),
        MatrixRow("base", "home", {"EDITOR": "nvim"}),
    ]
    report = MatrixReport(rows=rows, keys=["EDITOR"])
    assert "EDITOR" in report.summary()


# ---------------------------------------------------------------------------
# build_matrix integration tests (with patched resolve)
# ---------------------------------------------------------------------------

def test_build_matrix_unknown_profile_raises(profiles, environments, monkeypatch):
    monkeypatch.setattr("dotpull.matrix.resolve_variables", _fake_resolve)
    with pytest.raises(KeyError, match="unknown"):
        build_matrix("unknown", profiles, environments)


def test_build_matrix_creates_one_row_per_environment(profiles, environments, monkeypatch):
    monkeypatch.setattr("dotpull.matrix.resolve_variables", _fake_resolve)
    report = build_matrix("base", profiles, environments)
    assert len(report.rows) == len(environments)


def test_build_matrix_detects_differing_editor(profiles, environments, monkeypatch):
    monkeypatch.setattr("dotpull.matrix.resolve_variables", _fake_resolve)
    report = build_matrix("base", profiles, environments)
    assert "EDITOR" in report.differing_keys()


def test_build_matrix_shell_same_across_envs(profiles, environments, monkeypatch):
    monkeypatch.setattr("dotpull.matrix.resolve_variables", _fake_resolve)
    report = build_matrix("base", profiles, environments)
    assert "SHELL" not in report.differing_keys()
