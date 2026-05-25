"""Tests for dotpull.lint."""
from __future__ import annotations

from pathlib import Path

import pytest

from dotpull.lint import LintIssue, LintReport, lint_all, lint_profile


class _FakeProfile:
    def __init__(self, name, files=None, variables=None):
        self.name = name
        self.files = files or {}
        self.variables = variables or {}


@pytest.fixture()
def dotfiles_dir(tmp_path):
    return tmp_path


def test_report_healthy_when_no_errors():
    report = LintReport()
    report.add("warning", "default", "some warning")
    assert report.healthy


def test_report_not_healthy_when_error():
    report = LintReport()
    report.add("error", "default", "bad thing")
    assert not report.healthy


def test_report_summary_counts():
    report = LintReport()
    report.add("error", "p", "e1")
    report.add("warning", "p", "w1")
    report.add("warning", "p", "w2")
    assert report.summary == "1 error(s), 2 warning(s)"


def test_lint_profile_no_files_is_warning(dotfiles_dir):
    profile = _FakeProfile(name="empty")
    report = lint_profile(profile, dotfiles_dir)
    assert any(i.level == "warning" and "no files" in i.message for i in report.issues)


def test_lint_profile_missing_source_is_error(dotfiles_dir):
    profile = _FakeProfile(name="p", files={"missing.zshrc": "~/.zshrc"})
    report = lint_profile(profile, dotfiles_dir)
    assert any(i.level == "error" and "missing.zshrc" in i.message for i in report.issues)


def test_lint_profile_existing_source_no_error(dotfiles_dir):
    src = dotfiles_dir / "real.zshrc"
    src.write_text("export FOO=1")
    profile = _FakeProfile(name="p", files={"real.zshrc": "~/.zshrc"})
    report = lint_profile(profile, dotfiles_dir)
    errors = [i for i in report.issues if i.level == "error"]
    assert not errors


def test_lint_profile_duplicate_target_is_error(dotfiles_dir):
    (dotfiles_dir / "a.zshrc").write_text("a")
    (dotfiles_dir / "b.zshrc").write_text("b")
    profile = _FakeProfile(
        name="p",
        files={"a.zshrc": "~/.zshrc", "b.zshrc": "~/.zshrc"},
    )
    report = lint_profile(profile, dotfiles_dir)
    assert any("duplicate target" in i.message for i in report.issues)


def test_lint_profile_relative_target_is_warning(dotfiles_dir):
    src = dotfiles_dir / "rel.conf"
    src.write_text("x")
    profile = _FakeProfile(name="p", files={"rel.conf": "relative/path"})
    report = lint_profile(profile, dotfiles_dir)
    assert any(i.level == "warning" and "relative" in i.message for i in report.issues)


def test_lint_profile_null_variable_is_warning(dotfiles_dir):
    profile = _FakeProfile(name="p", variables={"MY_VAR": None})
    report = lint_profile(profile, dotfiles_dir)
    assert any(i.level == "warning" and "MY_VAR" in i.message for i in report.issues)


def test_lint_all_aggregates_profiles(dotfiles_dir):
    p1 = _FakeProfile(name="a")
    p2 = _FakeProfile(name="b")
    report = lint_all({"a": p1, "b": p2}, dotfiles_dir)
    profile_names = {i.profile for i in report.issues}
    assert "a" in profile_names and "b" in profile_names
