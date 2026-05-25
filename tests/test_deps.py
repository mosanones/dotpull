"""Tests for dotpull.deps — dependency checking."""
from unittest.mock import patch

import pytest

from dotpull.deps import DepResult, DepsReport, check_dep, check_all_deps


def test_check_dep_found(tmp_path):
    """check_dep returns found=True when shutil.which resolves the binary."""
    with patch("dotpull.deps.shutil.which", return_value="/usr/bin/git"):
        result = check_dep("git", required=True, note="vcs")
    assert result.found is True
    assert result.path == "/usr/bin/git"
    assert result.name == "git"
    assert result.ok is True


def test_check_dep_missing_required():
    """check_dep returns found=False and ok=False for a missing required dep."""
    with patch("dotpull.deps.shutil.which", return_value=None):
        result = check_dep("nonexistent-tool", required=True)
    assert result.found is False
    assert result.ok is False


def test_check_dep_missing_optional():
    """Missing optional dep is still ok."""
    with patch("dotpull.deps.shutil.which", return_value=None):
        result = check_dep("rsync", required=False)
    assert result.found is False
    assert result.ok is True


def test_deps_report_healthy_when_all_found():
    results = [
        DepResult(name="git", required=True, found=True, path="/usr/bin/git"),
        DepResult(name="diff", required=False, found=True, path="/usr/bin/diff"),
    ]
    report = DepsReport(results=results)
    assert report.healthy is True


def test_deps_report_not_healthy_when_required_missing():
    results = [
        DepResult(name="git", required=True, found=False),
    ]
    report = DepsReport(results=results)
    assert report.healthy is False


def test_deps_report_healthy_when_only_optional_missing():
    results = [
        DepResult(name="git", required=True, found=True, path="/usr/bin/git"),
        DepResult(name="gpg", required=False, found=False),
    ]
    report = DepsReport(results=results)
    assert report.healthy is True


def test_deps_report_summary_contains_names():
    results = [
        DepResult(name="git", required=True, found=True, path="/usr/bin/git", note="vcs"),
        DepResult(name="gpg", required=False, found=False, note="encryption"),
    ]
    report = DepsReport(results=results)
    summary = report.summary()
    assert "git" in summary
    assert "gpg" in summary
    assert "/usr/bin/git" in summary
    assert "encryption" in summary


def test_check_all_deps_returns_report():
    """check_all_deps returns a DepsReport with at least the built-in entries."""
    with patch("dotpull.deps.shutil.which", side_effect=lambda n: f"/usr/bin/{n}"):
        report = check_all_deps()
    assert isinstance(report, DepsReport)
    names = [r.name for r in report.results]
    assert "git" in names
    assert "diff" in names


def test_check_all_deps_accepts_extra():
    extra = [{"name": "mytool", "required": False, "note": "custom"}]
    with patch("dotpull.deps.shutil.which", return_value=None):
        report = check_all_deps(extra=extra)
    names = [r.name for r in report.results]
    assert "mytool" in names
