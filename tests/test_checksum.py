"""Tests for dotpull.checksum."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotpull.checksum import (
    ChecksumEntry,
    ChecksumError,
    ChecksumReport,
    _file_checksum,
    _store_path,
    compute_checksums,
    load_checksums,
    save_checksums,
    verify_checksums,
)


@pytest.fixture
def dotfiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


def _write(dotfiles_dir: Path, name: str, content: str) -> Path:
    p = dotfiles_dir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def test_file_checksum_is_stable(dotfiles_dir: Path):
    f = _write(dotfiles_dir, "a.txt", "hello")
    h1 = _file_checksum(f)
    h2 = _file_checksum(f)
    assert h1 == h2
    assert len(h1) == 64


def test_file_checksum_differs_for_different_content(dotfiles_dir: Path):
    f1 = _write(dotfiles_dir, "a.txt", "hello")
    f2 = _write(dotfiles_dir, "b.txt", "world")
    assert _file_checksum(f1) != _file_checksum(f2)


def test_compute_checksums_returns_entries(dotfiles_dir: Path):
    _write(dotfiles_dir, "vim/.vimrc", "set nu")
    entries = compute_checksums(dotfiles_dir, ["vim/.vimrc"])
    assert len(entries) == 1
    assert entries[0].path == "vim/.vimrc"
    assert len(entries[0].sha256) == 64


def test_compute_checksums_raises_on_missing_file(dotfiles_dir: Path):
    with pytest.raises(ChecksumError, match="Source file not found"):
        compute_checksums(dotfiles_dir, ["nonexistent.txt"])


def test_save_and_load_roundtrip(dotfiles_dir: Path):
    _write(dotfiles_dir, "a.txt", "data")
    entries = compute_checksums(dotfiles_dir, ["a.txt"])
    save_checksums(dotfiles_dir, entries)
    stored = load_checksums(dotfiles_dir)
    assert "a.txt" in stored
    assert stored["a.txt"] == entries[0].sha256


def test_load_checksums_returns_empty_when_no_file(dotfiles_dir: Path):
    result = load_checksums(dotfiles_dir)
    assert result == {}


def test_verify_checksums_healthy_when_unchanged(dotfiles_dir: Path):
    _write(dotfiles_dir, "z.txt", "stable")
    entries = compute_checksums(dotfiles_dir, ["z.txt"])
    save_checksums(dotfiles_dir, entries)
    report = verify_checksums(dotfiles_dir, ["z.txt"])
    assert report.healthy()
    assert "OK" in report.summary()


def test_verify_checksums_detects_change(dotfiles_dir: Path):
    f = _write(dotfiles_dir, "c.txt", "original")
    entries = compute_checksums(dotfiles_dir, ["c.txt"])
    save_checksums(dotfiles_dir, entries)
    f.write_text("modified")
    report = verify_checksums(dotfiles_dir, ["c.txt"])
    assert not report.healthy()
    assert "c.txt" in report.mismatches


def test_verify_checksums_mismatch_on_missing_stored(dotfiles_dir: Path):
    _write(dotfiles_dir, "d.txt", "new file")
    report = verify_checksums(dotfiles_dir, ["d.txt"])
    assert not report.healthy()
    assert "d.txt" in report.mismatches


def test_checksum_entry_roundtrip():
    e = ChecksumEntry(path="foo/bar", sha256="abc123")
    assert ChecksumEntry.from_dict(e.to_dict()) == e


def test_report_summary_with_mismatches():
    r = ChecksumReport(
        entries=[ChecksumEntry("a", "x"), ChecksumEntry("b", "y")],
        mismatches=["a"],
    )
    assert not r.healthy()
    assert "1 mismatch" in r.summary()
