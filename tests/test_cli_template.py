"""Tests for the template CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from dotpull.cli_template import template_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def dotpull_env(tmp_path):
    """Create a minimal dotpull environment with a config and a template file."""
    config_file = tmp_path / "dotpull.toml"
    config_file.write_text(
        '[dotfiles]\ndir = "/tmp/dots"\n\n'
        '[profiles.default]\n[profiles.default.variables]\n'
        'EDITOR = "vim"\nSHELL = "zsh"\n'
        '[profiles.work]\nextends = "default"\n[profiles.work.variables]\n'
        'EDITOR = "emacs"\n'
    )
    template_file = tmp_path / "bashrc.tmpl"
    template_file.write_text("export EDITOR={{ EDITOR }}\nexport SHELL={{ SHELL }}\n")
    return tmp_path, config_file, template_file


def test_render_uses_default_profile(runner, dotpull_env):
    tmp_path, config_file, template_file = dotpull_env
    result = runner.invoke(
        template_group,
        ["render", str(template_file), "--config", str(config_file)],
    )
    assert result.exit_code == 0
    assert "export EDITOR=vim" in result.output
    assert "export SHELL=zsh" in result.output


def test_render_uses_named_profile(runner, dotpull_env):
    tmp_path, config_file, template_file = dotpull_env
    result = runner.invoke(
        template_group,
        ["render", str(template_file), "--config", str(config_file), "--profile", "work"],
    )
    assert result.exit_code == 0
    assert "export EDITOR=emacs" in result.output
    assert "export SHELL=zsh" in result.output


def test_render_unknown_profile_exits(runner, dotpull_env):
    tmp_path, config_file, template_file = dotpull_env
    result = runner.invoke(
        template_group,
        ["render", str(template_file), "--config", str(config_file), "--profile", "nonexistent"],
    )
    assert result.exit_code != 0


def test_render_output_to_file(runner, dotpull_env, tmp_path):
    _, config_file, template_file = dotpull_env
    out_file = tmp_path / "rendered_bashrc"
    result = runner.invoke(
        template_group,
        ["render", str(template_file), "--config", str(config_file), "--output", str(out_file)],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    assert "export EDITOR=vim" in out_file.read_text()


def test_vars_lists_placeholders(runner, dotpull_env):
    _, _, template_file = dotpull_env
    result = runner.invoke(template_group, ["vars", str(template_file)])
    assert result.exit_code == 0
    assert "EDITOR" in result.output
    assert "SHELL" in result.output


def test_vars_no_placeholders(runner, tmp_path):
    plain = tmp_path / "plain.txt"
    plain.write_text("no placeholders here\n")
    result = runner.invoke(template_group, ["vars", str(plain)])
    assert result.exit_code == 0
    assert "No template variables found" in result.output
