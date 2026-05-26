"""Tests for dotpull.fmt — YAML formatter."""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from dotpull.fmt import FmtError, FmtResult, FmtReport, fmt_file, fmt_directory


@pytest.fixture()
def tmp_yaml(tmp_path: Path):
    """Return a helper that writes a YAML file and returns its path."""
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_fmt_file_no_change_when_already_canonical(tmp_yaml):
    canonical = "a: 1\nb: 2\n"
    p = tmp_yaml("clean.yaml", canonical)
    result = fmt_file(p)
    assert not result.changed
    assert result.summary().startswith("ok:")


def test_fmt_file_reformats_unsorted_keys(tmp_yaml):
    p = tmp_yaml("unsorted.yaml", "z: 3\na: 1\n")
    result = fmt_file(p)
    assert result.changed
    data = yaml.safe_load(p.read_text())
    assert list(data.keys()) == sorted(data.keys())


def test_fmt_file_dry_run_does_not_write(tmp_yaml):
    original = "z: 3\na: 1\n"
    p = tmp_yaml("dry.yaml", original)
    result = fmt_file(p, dry_run=True)
    assert result.changed
    assert p.read_text() == original  # unchanged on disk
    assert "dry-run" in result.summary()


def test_fmt_file_missing_raises(tmp_path):
    with pytest.raises(FmtError, match="not found"):
        fmt_file(tmp_path / "ghost.yaml")


def test_fmt_file_invalid_yaml_raises(tmp_yaml):
    p = tmp_yaml("bad.yaml", ": : : invalid")
    with pytest.raises(FmtError, match="YAML parse error"):
        fmt_file(p)


def test_fmt_file_empty_file_treated_as_empty_dict(tmp_yaml):
    p = tmp_yaml("empty.yaml", "")
    result = fmt_file(p)
    # empty dict dumps to '{}
    assert p.read_text().strip() == "{}"


def test_fmt_directory_formats_all_yaml_files(tmp_path):
    (tmp_path / "a.yaml").write_text("z: 1\na: 2\n")
    (tmp_path / "b.yaml").write_text("m: 9\nb: 0\n")
    report = fmt_directory(tmp_path)
    assert isinstance(report, FmtReport)
    assert len(report.results) == 2
    assert all(r.changed for r in report.results)


def test_fmt_directory_missing_dir_raises(tmp_path):
    with pytest.raises(FmtError, match="Directory not found"):
        fmt_directory(tmp_path / "nonexistent")


def test_fmt_report_summary_no_changes(tmp_path):
    (tmp_path / "c.yaml").write_text("a: 1\n")
    report = fmt_directory(tmp_path)
    # already canonical
    assert "already well-formatted" in report.summary()


def test_fmt_report_changed_files_list(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text("z: 9\na: 1\n")
    report = fmt_directory(tmp_path)
    assert p in report.changed_files()
    assert not report.healthy  # changed=True and not dry_run means healthy=False
