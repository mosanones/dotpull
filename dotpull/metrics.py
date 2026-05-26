"""Collect and report basic usage metrics for profiles and operations."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


_METRICS_FILE = ".dotpull_metrics.json"


@dataclass
class MetricEntry:
    operation: str
    profile: str
    file_count: int
    success: bool
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "MetricEntry":
        return MetricEntry(**d)


@dataclass
class MetricsReport:
    entries: List[MetricEntry] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def successes(self) -> int:
        return sum(1 for e in self.entries if e.success)

    @property
    def failures(self) -> int:
        return self.total - self.successes

    def by_profile(self) -> Dict[str, List[MetricEntry]]:
        result: Dict[str, List[MetricEntry]] = {}
        for entry in self.entries:
            result.setdefault(entry.profile, []).append(entry)
        return result

    def summary(self) -> str:
        return f"{self.total} operations: {self.successes} ok, {self.failures} failed"


def _metrics_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / _METRICS_FILE


def load_metrics(dotfiles_dir: Path) -> MetricsReport:
    path = _metrics_path(dotfiles_dir)
    if not path.exists():
        return MetricsReport()
    try:
        data = json.loads(path.read_text())
        entries = [MetricEntry.from_dict(e) for e in data.get("entries", [])]
        return MetricsReport(entries=entries)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"Corrupt metrics file: {exc}") from exc


def record_metric(
    dotfiles_dir: Path,
    operation: str,
    profile: str,
    file_count: int,
    success: bool,
    timestamp: Optional[str] = None,
) -> MetricEntry:
    import datetime

    ts = timestamp or datetime.datetime.utcnow().isoformat()
    entry = MetricEntry(
        operation=operation,
        profile=profile,
        file_count=file_count,
        success=success,
        timestamp=ts,
    )
    report = load_metrics(dotfiles_dir)
    report.entries.append(entry)
    path = _metrics_path(dotfiles_dir)
    path.write_text(json.dumps({"entries": [e.to_dict() for e in report.entries]}, indent=2))
    return entry


def clear_metrics(dotfiles_dir: Path) -> None:
    path = _metrics_path(dotfiles_dir)
    if path.exists():
        path.unlink()
