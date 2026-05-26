"""Tests for dotpull.metrics."""
import json
import pytest
from pathlib import Path

from dotpull.metrics import (
    load_metrics,
    record_metric,
    clear_metrics,
    MetricsReport,
    MetricEntry,
)


@pytest.fixture
def dotfiles_dir(tmp_path: Path) -> Path:
    dotfiles_dir = tmp_path / "dotfiles"
    dotfiles_dir.mkdir()
    return dotfiles_dir


def test_load_metrics_returns_empty_when_no_file(dotfiles_dir):
    report = load_metrics(dotfiles_dir)
    assert isinstance(report, MetricsReport)
    assert report.total == 0


def test_record_metric_creates_entry(dotfiles_dir):
    entry = record_metric(dotfiles_dir, "sync", "default", 3, True)
    assert isinstance(entry, MetricEntry)
    assert entry.operation == "sync"
    assert entry.profile == "default"
    assert entry.file_count == 3
    assert entry.success is True


def test_record_metric_persists_to_disk(dotfiles_dir):
    record_metric(dotfiles_dir, "link", "work", 5, True)
    report = load_metrics(dotfiles_dir)
    assert report.total == 1
    assert report.entries[0].operation == "link"


def test_record_multiple_entries(dotfiles_dir):
    record_metric(dotfiles_dir, "sync", "default", 2, True)
    record_metric(dotfiles_dir, "sync", "default", 2, False)
    report = load_metrics(dotfiles_dir)
    assert report.total == 2
    assert report.successes == 1
    assert report.failures == 1


def test_summary_string(dotfiles_dir):
    record_metric(dotfiles_dir, "sync", "default", 1, True)
    record_metric(dotfiles_dir, "sync", "work", 1, False)
    report = load_metrics(dotfiles_dir)
    assert "2 operations" in report.summary()
    assert "1 ok" in report.summary()
    assert "1 failed" in report.summary()


def test_by_profile_groups_correctly(dotfiles_dir):
    record_metric(dotfiles_dir, "sync", "default", 1, True)
    record_metric(dotfiles_dir, "sync", "work", 2, True)
    record_metric(dotfiles_dir, "link", "default", 1, False)
    report = load_metrics(dotfiles_dir)
    grouped = report.by_profile()
    assert len(grouped["default"]) == 2
    assert len(grouped["work"]) == 1


def test_clear_metrics_removes_file(dotfiles_dir):
    record_metric(dotfiles_dir, "sync", "default", 1, True)
    clear_metrics(dotfiles_dir)
    report = load_metrics(dotfiles_dir)
    assert report.total == 0


def test_load_metrics_raises_on_corrupt_file(dotfiles_dir):
    metrics_file = dotfiles_dir / ".dotpull_metrics.json"
    metrics_file.write_text("not valid json{{{")
    with pytest.raises(ValueError, match="Corrupt metrics file"):
        load_metrics(dotfiles_dir)


def test_metric_entry_roundtrip():
    entry = MetricEntry(
        operation="export",
        profile="personal",
        file_count=7,
        success=True,
        timestamp="2024-01-01T00:00:00",
    )
    assert MetricEntry.from_dict(entry.to_dict()) == entry
