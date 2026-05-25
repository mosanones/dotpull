"""Tests for dotpull.cli_env."""

from __future__ import annotations

import os

import pytest
from click.testing import CliRunner

from dotpull.cli_env import env_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path, monkeypatch):
    """Minimal dotpull.yaml in a temp dir."""
    cfg = tmp_path / "dotpull.yaml"
    cfg.write_text(
        f"dotfiles_dir: {tmp_path / 'dotfiles'}\n"
        "default_profile: base\n"
    )
    (tmp_path / "dotfiles").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# cmd_show
# ---------------------------------------------------------------------------

def test_show_no_prefix_prints_env(runner, dotpull_env, monkeypatch):
    monkeypatch.setenv("DOTPULL_SHOW_TEST", "visible")
    result = runner.invoke(env_group, ["show", "--config", "dotpull.yaml"])
    assert result.exit_code == 0
    assert "DOTPULL_SHOW_TEST=visible" in result.output


def test_show_with_prefix_filters(runner, dotpull_env, monkeypatch):
    monkeypatch.setenv("DP_KEEP", "yes")
    monkeypatch.setenv("OTHER_DROP", "no")
    result = runner.invoke(
        env_group,
        ["show", "--config", "dotpull.yaml", "--prefix", "DP_"],
    )
    assert result.exit_code == 0
    assert "DP_KEEP=yes" in result.output
    assert "OTHER_DROP" not in result.output


def test_show_no_matches_prints_message(runner, dotpull_env):
    result = runner.invoke(
        env_group,
        ["show", "--config", "dotpull.yaml", "--prefix", "ZZZNOMATCH_"],
    )
    assert result.exit_code == 0
    assert "No matching" in result.output


# ---------------------------------------------------------------------------
# cmd_check
# ---------------------------------------------------------------------------

def test_check_present_variables_exits_zero(runner, dotpull_env, monkeypatch):
    monkeypatch.setenv("DOTPULL_CHECK_VAR", "ok")
    result = runner.invoke(
        env_group,
        ["check", "DOTPULL_CHECK_VAR", "--config", "dotpull.yaml"],
    )
    assert result.exit_code == 0
    assert "DOTPULL_CHECK_VAR=ok" in result.output
    assert "1 variable(s) present" in result.output


def test_check_missing_variable_exits_nonzero(runner, dotpull_env, monkeypatch):
    monkeypatch.delenv("DOTPULL_ABSENT_VAR", raising=False)
    result = runner.invoke(
        env_group,
        ["check", "DOTPULL_ABSENT_VAR", "--config", "dotpull.yaml"],
    )
    assert result.exit_code != 0
    assert "DOTPULL_ABSENT_VAR" in result.output
