"""Tests for dotpull.cli_export."""

import tarfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from dotpull.cli_export import export_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def dotpull_env(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    (dotfiles / "bashrc").write_text("# bash\n")

    cfg = tmp_path / "dotpull.toml"
    cfg.write_text(
        f'dotfiles_dir = "{dotfiles}"\n'
        'default_profile = "base"\n'
        '[profiles.base]\n'
        'files = ["bashrc"]\n'
    )
    return {"config": str(cfg), "dotfiles": dotfiles, "root": tmp_path}


def test_create_export_success(runner, dotpull_env):
    output = str(dotpull_env["root"] / "out")
    result = runner.invoke(
        export_group,
        ["create", "--config", dotpull_env["config"], "--output", output],
    )
    assert result.exit_code == 0, result.output
    assert "Exported to" in result.output


def test_create_export_with_label(runner, dotpull_env):
    output = str(dotpull_env["root"] / "out")
    result = runner.invoke(
        export_group,
        ["create", "--config", dotpull_env["config"], "--label", "release", "--output", output],
    )
    assert result.exit_code == 0
    assert "release" in result.output


def test_create_export_unknown_profile(runner, dotpull_env):
    output = str(dotpull_env["root"] / "out")
    result = runner.invoke(
        export_group,
        ["create", "--config", dotpull_env["config"], "--profile", "ghost", "--output", output],
    )
    assert result.exit_code != 0
    assert "Unknown profile" in result.output


def test_import_restores_files(runner, dotpull_env):
    output_dir = dotpull_env["root"] / "out"
    # first create
    runner.invoke(
        export_group,
        ["create", "--config", dotpull_env["config"], "--output", str(output_dir)],
    )
    archives = list(output_dir.glob("*.tar.gz"))
    assert archives, "no archive produced"

    restore_dir = dotpull_env["root"] / "restored_dotfiles"
    restore_dir.mkdir()
    # patch config dotfiles_dir to restore location
    cfg2 = dotpull_env["root"] / "dotpull2.toml"
    cfg2.write_text(
        f'dotfiles_dir = "{restore_dir}"\n'
        'default_profile = "base"\n'
        '[profiles.base]\nfiles = ["bashrc"]\n'
    )
    result = runner.invoke(
        export_group,
        ["import", str(archives[0]), "--config", str(cfg2)],
    )
    assert result.exit_code == 0, result.output
    assert "Restored" in result.output
