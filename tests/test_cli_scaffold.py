"""Tests for dotpull.cli_scaffold."""
from __future__ import annotations

import yaml
import pytest
from pathlib import Path
from click.testing import CliRunner

from dotpull.cli_scaffold import scaffold_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    profiles = {"base": {"files": [], "variables": {}, "extends": None}}
    (dotfiles / "profiles.yaml").write_text(yaml.dump(profiles))
    config = {"dotfiles_dir": str(dotfiles), "default_profile": "base"}
    config_path = tmp_path / "dotpull.yaml"
    config_path.write_text(yaml.dump(config))
    return {"config": str(config_path), "dotfiles": dotfiles}


def test_create_scaffold_success(runner, dotpull_env):
    result = runner.invoke(
        scaffold_group,
        ["create", "work", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    data = yaml.safe_load(
        (dotpull_env["dotfiles"] / "profiles.yaml").read_text()
    )
    assert "work" in data


def test_create_scaffold_with_file_stub(runner, dotpull_env):
    result = runner.invoke(
        scaffold_group,
        ["create", "laptop", "--file", "home/.vimrc",
         "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert (dotpull_env["dotfiles"] / "home" / ".vimrc").exists()


def test_create_scaffold_dry_run_no_write(runner, dotpull_env):
    result = runner.invoke(
        scaffold_group,
        ["create", "preview", "--file", "home/.bashrc",
         "--dry-run", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    data = yaml.safe_load(
        (dotpull_env["dotfiles"] / "profiles.yaml").read_text()
    )
    assert "preview" not in data
    assert not (dotpull_env["dotfiles"] / "home" / ".bashrc").exists()


def test_create_scaffold_duplicate_profile_exits_nonzero(runner, dotpull_env):
    result = runner.invoke(
        scaffold_group,
        ["create", "base", "--config", dotpull_env["config"]],
    )
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_create_scaffold_output_contains_profile_name(runner, dotpull_env):
    result = runner.invoke(
        scaffold_group,
        ["create", "server", "--config", dotpull_env["config"]],
    )
    assert "server" in result.output
