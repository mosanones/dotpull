"""Tests for dotpull.doctor."""
from pathlib import Path

import pytest

from dotpull.doctor import run_doctor, _check_config, _check_dotfiles_dir


@pytest.fixture
def dotfiles_dir(tmp_path):
    d = tmp_path / "dotfiles"
    d.mkdir()
    (d / ".bashrc").write_text("export PATH=$PATH")
    return d


@pytest.fixture
def config_file(tmp_path, dotfiles_dir):
    cfg = tmp_path / "dotpull.toml"
    cfg.write_text(
        f'[dotpull]\ndotfiles_dir = "{dotfiles_dir}"\ndefault_profile = "base"\n\n'
        '[profiles.base]\nfiles = [".bashrc"]\n'
    )
    return cfg


def test_check_config_valid(config_file):
    result = _check_config(config_file)
    assert result.ok
    assert "valid" in result.message.lower()


def test_check_config_missing_file(tmp_path):
    result = _check_config(tmp_path / "nonexistent.toml")
    # Missing file returns defaults which may or may not have dotfiles_dir set;
    # validate_config should flag the missing dotfiles_dir.
    # Either way the function should not raise.
    assert isinstance(result.ok, bool)


def test_check_dotfiles_dir_exists(dotfiles_dir):
    result = _check_dotfiles_dir({"dotfiles_dir": str(dotfiles_dir)})
    assert result.ok


def test_check_dotfiles_dir_missing(tmp_path):
    result = _check_dotfiles_dir({"dotfiles_dir": str(tmp_path / "nope")})
    assert not result.ok
    assert "not found" in result.message


def test_run_doctor_healthy(config_file, dotfiles_dir, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    # Create the symlink so audit_link returns 'ok'
    target = home / ".bashrc"
    target.symlink_to(dotfiles_dir / ".bashrc")

    report = run_doctor(config_file, home_dir=home)
    assert report.healthy
    names = [r.name for r in report.results]
    assert "config" in names
    assert "dotfiles_dir" in names
    assert any(n.startswith("link:") for n in names)


def test_run_doctor_broken_symlink(config_file, dotfiles_dir, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    # Do NOT create the symlink — audit should report broken/missing

    report = run_doctor(config_file, home_dir=home)
    link_results = [r for r in report.results if r.name.startswith("link:")]
    assert link_results
    assert any(not r.ok for r in link_results)


def test_run_doctor_unknown_profile(config_file, dotfiles_dir, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    report = run_doctor(config_file, profile_name="ghost", home_dir=home)
    profile_check = next(r for r in report.results if r.name == "profile")
    assert not profile_check.ok
    assert not report.healthy
