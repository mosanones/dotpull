"""Tests for dotpull.resolve and dotpull.cli_resolve."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from dotpull.profile import Profile
from dotpull.resolve import resolve_variables, ResolvedVars
from dotpull.cli_resolve import resolve_group


# ---------------------------------------------------------------------------
# Unit tests for resolve_variables
# ---------------------------------------------------------------------------

def _profile(name: str, data: dict) -> Profile:
    return Profile(name, data)


def test_resolve_uses_global_config_vars():
    cfg = {"variables": {"editor": "vim"}}
    p = _profile("default", {})
    rv = resolve_variables(p, cfg)
    assert rv.variables["editor"] == "vim"
    assert rv.sources["editor"] == "config"


def test_resolve_profile_vars_override_config():
    cfg = {"variables": {"editor": "vim"}, "profiles": {"work": {"variables": {"editor": "nvim"}}}}
    p = _profile("work", {"variables": {"editor": "nvim"}})
    rv = resolve_variables(p, cfg)
    assert rv.variables["editor"] == "nvim"
    assert rv.sources["editor"] == "profile:work"


def test_resolve_parent_vars_between_config_and_profile():
    cfg = {
        "variables": {"shell": "sh"},
        "profiles": {
            "base": {"variables": {"shell": "bash"}},
            "dev": {"extends": "base", "variables": {}},
        },
    }
    p = _profile("dev", {"extends": "base", "variables": {}})
    rv = resolve_variables(p, cfg)
    assert rv.variables["shell"] == "bash"
    assert rv.sources["shell"] == "profile:base"


def test_resolve_env_vars_highest_priority(monkeypatch):
    monkeypatch.setenv("DOTPULL_EDITOR", "emacs")
    cfg = {"variables": {"editor": "vim"}}
    p = _profile("default", {"variables": {"editor": "nano"}})
    rv = resolve_variables(p, cfg, include_env=True)
    assert rv.variables["editor"] == "emacs"
    assert "env:DOTPULL_EDITOR" in rv.sources["editor"]


def test_resolve_env_vars_excluded_by_default(monkeypatch):
    monkeypatch.setenv("DOTPULL_EDITOR", "emacs")
    cfg = {"variables": {"editor": "vim"}}
    p = _profile("default", {})
    rv = resolve_variables(p, cfg, include_env=False)
    assert rv.variables["editor"] == "vim"


def test_resolve_empty_config_and_profile():
    rv = resolve_variables(_profile("x", {}), {})
    assert isinstance(rv, ResolvedVars)
    assert rv.variables == {}


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path):
    cfg = tmp_path / "dotpull.toml"
    cfg.write_text(
        '[variables]\nshell = "zsh"\n\n'
        '[profiles.main]\n[profiles.main.variables]\neditor = "vim"\n'
    )
    return str(cfg)


def test_show_prints_variables(runner, dotpull_env):
    result = runner.invoke(resolve_group, ["show", "--config", dotpull_env, "--profile", "main"])
    assert result.exit_code == 0
    assert "editor" in result.output
    assert "vim" in result.output
    assert "shell" in result.output


def test_show_unknown_profile_exits(runner, dotpull_env):
    result = runner.invoke(resolve_group, ["show", "--config", dotpull_env, "--profile", "ghost"])
    assert result.exit_code != 0
    assert "Unknown profile" in result.output


def test_get_returns_value(runner, dotpull_env):
    result = runner.invoke(resolve_group, ["get", "editor", "--config", dotpull_env, "--profile", "main"])
    assert result.exit_code == 0
    assert "vim" in result.output


def test_get_missing_key_exits(runner, dotpull_env):
    result = runner.invoke(resolve_group, ["get", "nonexistent", "--config", dotpull_env, "--profile", "main"])
    assert result.exit_code != 0
    assert "not found" in result.output
