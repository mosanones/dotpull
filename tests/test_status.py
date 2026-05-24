"""Tests for dotpull.status and dotpull.cli_status."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from dotpull.profile import Profile
from dotpull.status import check_profile_status, ProfileStatus
from dotpull.cli_status import status_group


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


@pytest.fixture()
def home_dir(tmp_path: Path) -> Path:
    h = tmp_path / "home"
    h.mkdir()
    return h


@pytest.fixture()
def simple_profile(dotfiles_dir: Path) -> Profile:
    src = dotfiles_dir / ".bashrc"
    src.write_text("export PATH=~/bin:$PATH\n")
    return Profile(name="default", files={".bashrc": "~/.bashrc"})


# ---------------------------------------------------------------------------
# Unit tests for check_profile_status
# ---------------------------------------------------------------------------

def test_status_all_synced(dotfiles_dir, home_dir, simple_profile):
    target = home_dir / ".bashrc"
    target.symlink_to(dotfiles_dir / ".bashrc")

    st = check_profile_status(simple_profile, dotfiles_dir, home_dir)
    assert st.healthy
    assert st.synced == 1
    assert st.missing == 0
    assert st.drifted == 0


def test_status_missing_target(dotfiles_dir, home_dir, simple_profile):
    st = check_profile_status(simple_profile, dotfiles_dir, home_dir)
    assert not st.healthy
    assert st.missing == 1


def test_status_drifted_not_symlink(dotfiles_dir, home_dir, simple_profile):
    target = home_dir / ".bashrc"
    target.write_text("export PATH=~/bin:$PATH\n")  # same content, but NOT a symlink

    st = check_profile_status(simple_profile, dotfiles_dir, home_dir)
    assert not st.healthy
    assert st.drifted == 1


def test_summary_string(dotfiles_dir, home_dir, simple_profile):
    st = check_profile_status(simple_profile, dotfiles_dir, home_dir)
    summary = st.summary()
    assert "profile=default" in summary
    assert "total=1" in summary


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path, dotfiles_dir, home_dir):
    cfg = tmp_path / "dotpull.toml"
    src = dotfiles_dir / ".vimrc"
    src.write_text('set number\n')
    cfg.write_text(
        f'dotfiles_dir = "{dotfiles_dir}"\n'
        f'[profiles.default]\n'
        f'files = {{".".vimrc" = "{home_dir}/.vimrc"}}\n'
    )
    return {"cfg": str(cfg), "home": str(home_dir), "dotfiles": dotfiles_dir, "home_dir": home_dir}


def test_cli_show_exits_2_when_not_synced(runner, dotpull_env):
    result = runner.invoke(
        status_group,
        ["show", "--config", dotpull_env["cfg"], "--home", dotpull_env["home"]],
    )
    assert result.exit_code == 2


def test_cli_show_unknown_profile_exits_1(runner, dotpull_env):
    result = runner.invoke(
        status_group,
        ["show", "--config", dotpull_env["cfg"], "--profile", "nonexistent",
         "--home", dotpull_env["home"]],
    )
    assert result.exit_code == 1
