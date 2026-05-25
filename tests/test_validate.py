"""Tests for dotpull.validate."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotpull.validate import ValidationIssue, validate_profile_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeProfile:
    """Minimal stand-in for Profile."""

    def __init__(self, name: str, files: list):
        self.name = name
        self.files = files


@pytest.fixture()
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_report_healthy_when_all_files_present(dotfiles_dir: Path) -> None:
    (dotfiles_dir / "bashrc").write_text("# bash")
    profile = _FakeProfile(
        name="default",
        files=[{"src": "bashrc", "target": "~/.bashrc"}],
    )
    report = validate_profile_files(profile, dotfiles_dir)
    assert report.healthy
    assert report.issues == []


def test_missing_source_is_error(dotfiles_dir: Path) -> None:
    profile = _FakeProfile(
        name="default",
        files=[{"src": "missing_file", "target": "~/.missing"}],
    )
    report = validate_profile_files(profile, dotfiles_dir)
    assert not report.healthy
    errors = [i for i in report.issues if i.severity == "error"]
    assert any("not found" in e.reason for e in errors)


def test_missing_target_is_error(dotfiles_dir: Path) -> None:
    (dotfiles_dir / "vimrc").write_text("set nu")
    profile = _FakeProfile(
        name="default",
        files=[{"src": "vimrc", "target": ""}],
    )
    report = validate_profile_files(profile, dotfiles_dir)
    assert not report.healthy
    assert any("target" in i.reason.lower() for i in report.issues)


def test_absolute_target_is_warning(dotfiles_dir: Path) -> None:
    (dotfiles_dir / "tmux.conf").write_text("set -g")
    profile = _FakeProfile(
        name="default",
        files=[{"src": "tmux.conf", "target": "/etc/tmux.conf"}],
    )
    report = validate_profile_files(profile, dotfiles_dir)
    assert report.healthy  # warning, not error
    warnings = [i for i in report.issues if i.severity == "warning"]
    assert len(warnings) == 1
    assert "absolute" in warnings[0].reason.lower()


def test_missing_src_key_is_error(dotfiles_dir: Path) -> None:
    profile = _FakeProfile(
        name="default",
        files=[{"target": "~/.bashrc"}],  # no 'src'
    )
    report = validate_profile_files(profile, dotfiles_dir)
    assert not report.healthy
    assert any("src" in i.reason.lower() for i in report.issues)


def test_summary_reflects_counts(dotfiles_dir: Path) -> None:
    profile = _FakeProfile(
        name="work",
        files=[
            {"src": "no_such_file", "target": "~/.x"},
        ],
    )
    report = validate_profile_files(profile, dotfiles_dir)
    assert "work" in report.summary
    assert "1 error" in report.summary


def test_summary_ok_when_healthy(dotfiles_dir: Path) -> None:
    (dotfiles_dir / "gitconfig").write_text("[user]")
    profile = _FakeProfile(
        name="home",
        files=[{"src": "gitconfig", "target": "~/.gitconfig"}],
    )
    report = validate_profile_files(profile, dotfiles_dir)
    assert "OK" in report.summary
