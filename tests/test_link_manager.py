"""Integration tests for dotpull.link_manager.LinkManager."""

import pytest
from pathlib import Path

from dotpull.link_manager import LinkManager
from dotpull.profile import Profile


@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    (d / ".bashrc").write_text("# bashrc")
    (d / ".vimrc").write_text("# vimrc")
    return d


@pytest.fixture()
def home_dir(tmp_path: Path) -> Path:
    h = tmp_path / "home"
    h.mkdir()
    return h


@pytest.fixture()
def simple_profile() -> Profile:
    return Profile(name="default", files=[".bashrc", ".vimrc"])


def test_apply_creates_symlinks(dotfiles_dir, home_dir, simple_profile):
    manager = LinkManager(dotfiles_dir, home_dir)
    results = manager.apply(simple_profile)
    assert all(r["status"] == "linked" for r in results)
    assert (home_dir / ".bashrc").is_symlink()
    assert (home_dir / ".vimrc").is_symlink()


def test_apply_returns_error_on_conflict(dotfiles_dir, home_dir, simple_profile):
    (home_dir / ".bashrc").write_text("existing")
    manager = LinkManager(dotfiles_dir, home_dir)
    results = manager.apply(simple_profile)
    errors = [r for r in results if r["status"] == "error"]
    assert len(errors) == 1
    assert ".bashrc" in errors[0]["error"]


def test_apply_force_overwrites(dotfiles_dir, home_dir, simple_profile):
    (home_dir / ".bashrc").write_text("existing")
    manager = LinkManager(dotfiles_dir, home_dir)
    results = manager.apply(simple_profile, force=True)
    assert all(r["status"] == "linked" for r in results)


def test_remove_unlinks(dotfiles_dir, home_dir, simple_profile):
    manager = LinkManager(dotfiles_dir, home_dir)
    manager.apply(simple_profile)
    results = manager.remove(simple_profile)
    assert all(r["removed"] for r in results)
    assert not (home_dir / ".bashrc").exists()


def test_audit_reports_ok_after_apply(dotfiles_dir, home_dir, simple_profile):
    manager = LinkManager(dotfiles_dir, home_dir)
    manager.apply(simple_profile)
    results = manager.audit(simple_profile)
    assert all(r["status"] == "ok" for r in results)


def test_audit_reports_missing_before_apply(dotfiles_dir, home_dir, simple_profile):
    manager = LinkManager(dotfiles_dir, home_dir)
    results = manager.audit(simple_profile)
    assert all(r["status"] == "missing" for r in results)
