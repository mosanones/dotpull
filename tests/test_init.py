"""Tests for dotpull.init and dotpull.cli_init."""

from __future__ import annotations

import pytest
import yaml
from click.testing import CliRunner
from pathlib import Path

from dotpull.init import init_dotfiles_dir, InitResult
from dotpull.cli_init import init_group


# ---------------------------------------------------------------------------
# init_dotfiles_dir unit tests
# ---------------------------------------------------------------------------


def test_init_creates_directory_structure(tmp_path):
    target = tmp_path / "dots"
    result = init_dotfiles_dir(target)

    assert result.success
    assert target.is_dir()
    assert (target / ".dotpull" / "snapshots").is_dir()
    assert (target / ".dotpull" / "backups").is_dir()


def test_init_writes_config_yaml(tmp_path):
    target = tmp_path / "dots"
    init_dotfiles_dir(target)

    config_path = target / "dotpull.yaml"
    assert config_path.exists()
    data = yaml.safe_load(config_path.read_text())
    assert "dotfiles_dir" in data
    assert "default_profile" in data


def test_init_writes_profiles_yaml(tmp_path):
    target = tmp_path / "dots"
    init_dotfiles_dir(target)

    profiles_path = target / "profiles.yaml"
    assert profiles_path.exists()
    data = yaml.safe_load(profiles_path.read_text())
    assert "default" in data


def test_init_skips_existing_files_without_force(tmp_path):
    target = tmp_path / "dots"
    init_dotfiles_dir(target)

    # Second call without force
    result = init_dotfiles_dir(target)
    assert result.success
    assert len(result.skipped) > 0
    assert len(result.created) == 0  # nothing new to create


def test_init_force_overwrites_existing(tmp_path):
    target = tmp_path / "dots"
    init_dotfiles_dir(target)

    config_path = target / "dotpull.yaml"
    config_path.write_text("corrupted: true")

    result = init_dotfiles_dir(target, force=True)
    assert result.success
    data = yaml.safe_load(config_path.read_text())
    assert "dotfiles_dir" in data


def test_init_writes_gitignore(tmp_path):
    target = tmp_path / "dots"
    init_dotfiles_dir(target)

    gitignore = target / ".gitignore"
    assert gitignore.exists()
    assert "backups" in gitignore.read_text()


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_create_success(runner, tmp_path):
    target = str(tmp_path / "dots")
    result = runner.invoke(init_group, ["create", target])
    assert result.exit_code == 0
    assert "Created" in result.output
    assert "ready" in result.output


def test_cli_create_skips_on_second_run(runner, tmp_path):
    target = str(tmp_path / "dots")
    runner.invoke(init_group, ["create", target])
    result = runner.invoke(init_group, ["create", target])
    assert result.exit_code == 0
    assert "Skipped" in result.output


def test_cli_create_force_flag(runner, tmp_path):
    target = str(tmp_path / "dots")
    runner.invoke(init_group, ["create", target])
    result = runner.invoke(init_group, ["create", "--force", target])
    assert result.exit_code == 0
    assert "Created" in result.output
