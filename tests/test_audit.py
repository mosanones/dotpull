"""Tests for dotpull.audit module."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from dotpull.audit import audit_profile, AuditReport, AuditEntry
from dotpull.link import AuditResult


@pytest.fixture
def dotfiles_dir(tmp_path):
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


@pytest.fixture
def home_dir(tmp_path):
    h = tmp_path / "home"
    h.mkdir()
    return h


@pytest.fixture
def simple_profile():
    profile = MagicMock()
    profile.name = "default"
    profile.resolve_files.return_value = {
        ".bashrc": ".bashrc",
        ".vimrc": ".vimrc",
    }
    return profile


def test_audit_report_healthy_when_all_ok():
    report = AuditReport(profile_name="default")
    report.entries = [
        AuditEntry(source=Path("a"), target=Path("b"), status="ok"),
        AuditEntry(source=Path("c"), target=Path("d"), status="ok"),
    ]
    assert report.healthy is True
    assert report.issues == []


def test_audit_report_not_healthy_with_conflict():
    report = AuditReport(profile_name="default")
    report.entries = [
        AuditEntry(source=Path("a"), target=Path("b"), status="ok"),
        AuditEntry(source=Path("c"), target=Path("d"), status="conflict", detail="file exists"),
    ]
    assert report.healthy is False
    assert len(report.issues) == 1
    assert report.issues[0].status == "conflict"


def test_audit_report_summary_string():
    report = AuditReport(profile_name="work")
    report.entries = [
        AuditEntry(source=Path("a"), target=Path("b"), status="ok"),
        AuditEntry(source=Path("c"), target=Path("d"), status="missing_target"),
    ]
    summary = report.summary()
    assert "1/2" in summary
    assert "work" in summary


def test_audit_profile_all_ok(dotfiles_dir, home_dir, simple_profile):
    ok_result = AuditResult(status="ok", detail=None)
    with patch("dotpull.audit.audit_link", return_value=ok_result):
        report = audit_profile(simple_profile, dotfiles_dir, home_dir)

    assert report.profile_name == "default"
    assert len(report.entries) == 2
    assert report.healthy is True


def test_audit_profile_with_conflict(dotfiles_dir, home_dir, simple_profile):
    conflict_result = AuditResult(status="conflict", detail="regular file exists")
    with patch("dotpull.audit.audit_link", return_value=conflict_result):
        report = audit_profile(simple_profile, dotfiles_dir, home_dir)

    assert not report.healthy
    assert all(e.status == "conflict" for e in report.entries)


def test_audit_profile_link_error_recorded(dotfiles_dir, home_dir, simple_profile):
    from dotpull.link import LinkError

    with patch("dotpull.audit.audit_link", side_effect=LinkError("unexpected")):
        report = audit_profile(simple_profile, dotfiles_dir, home_dir)

    assert all(e.status == "error" for e in report.entries)
    assert all("unexpected" in (e.detail or "") for e in report.entries)
