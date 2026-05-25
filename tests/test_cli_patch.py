"""Tests for dotpull.cli_patch."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch as mock_patch

import pytest
from click.testing import CliRunner

from dotpull.cli_patch import patch_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    (dotfiles / "bashrc").write_text("export PS1='$ '")

    config = tmp_path / "dotpull.yaml"
    config.write_text(
        f"dotfiles_dir: {dotfiles}\n"
        "profiles:\n"
        "  home:\n"
        "    files:\n"
        "      - bashrc\n"
    )
    return {"config": str(config), "dotfiles": dotfiles}


def test_apply_patches_no_patch_dir_skips(runner, dotpull_env):
    result = runner.invoke(
        patch_group,
        ["apply", "home", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "skipped" in result.output


def test_apply_patches_dry_run_prefix(runner, dotpull_env):
    with mock_patch("dotpull.cli_patch.apply_patches_for_profile") as m:
        from dotpull.patch import PatchResult
        m.return_value = PatchResult(success=True, patched=[], skipped=["bashrc"])
        result = runner.invoke(
            patch_group,
            ["apply", "home", "--config", dotpull_env["config"], "--dry-run"],
        )
    assert result.exit_code == 0
    assert "[dry-run]" in result.output


def test_apply_unknown_profile_exits(runner, dotpull_env):
    result = runner.invoke(
        patch_group,
        ["apply", "nonexistent", "--config", dotpull_env["config"]],
    )
    assert result.exit_code != 0
    assert "Unknown profile" in result.output


def test_apply_reports_errors_and_exits_nonzero(runner, dotpull_env):
    with mock_patch("dotpull.cli_patch.apply_patches_for_profile") as m:
        from dotpull.patch import PatchResult
        m.return_value = PatchResult(
            success=False, patched=[], skipped=[], errors=["bad patch"]
        )
        result = runner.invoke(
            patch_group,
            ["apply", "home", "--config", dotpull_env["config"]],
        )
    assert result.exit_code != 0
    assert "bad patch" in result.output


def test_list_patches_empty(runner, dotpull_env):
    result = runner.invoke(
        patch_group,
        ["list", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "No patches found" in result.output


def test_list_patches_shows_files(runner, dotpull_env):
    dotfiles = dotpull_env["dotfiles"]
    patch_dir = dotfiles / ".patches" / "home"
    patch_dir.mkdir(parents=True)
    (patch_dir / "bashrc.patch").write_text("")

    result = runner.invoke(
        patch_group,
        ["list", "--config", dotpull_env["config"], "--profile", "home"],
    )
    assert result.exit_code == 0
    assert "bashrc.patch" in result.output
