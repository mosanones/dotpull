"""Track and query the history of sync operations for profiles."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


HISTORY_FILE = ".history.json"


@dataclass
class HistoryEntry:
    profile: str
    action: str  # e.g. "sync", "link", "rollback"
    timestamp: str
    files_affected: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "HistoryEntry":
        return HistoryEntry(
            profile=d["profile"],
            action=d["action"],
            timestamp=d["timestamp"],
            files_affected=d.get("files_affected", []),
            note=d.get("note"),
        )


def _history_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / HISTORY_FILE


def load_history(dotfiles_dir: Path) -> List[HistoryEntry]:
    path = _history_path(dotfiles_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [HistoryEntry.from_dict(e) for e in data]
    except (json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"Corrupt history file: {exc}") from exc


def record_entry(dotfiles_dir: Path, entry: HistoryEntry) -> None:
    entries = load_history(dotfiles_dir)
    entries.append(entry)
    path = _history_path(dotfiles_dir)
    path.write_text(json.dumps([e.to_dict() for e in entries], indent=2))


def make_entry(
    profile: str,
    action: str,
    files_affected: Optional[List[str]] = None,
    note: Optional[str] = None,
) -> HistoryEntry:
    return HistoryEntry(
        profile=profile,
        action=action,
        timestamp=datetime.now(timezone.utc).isoformat(),
        files_affected=files_affected or [],
        note=note,
    )


def filter_history(
    entries: List[HistoryEntry],
    profile: Optional[str] = None,
    action: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[HistoryEntry]:
    result = entries
    if profile:
        result = [e for e in result if e.profile == profile]
    if action:
        result = [e for e in result if e.action == action]
    if limit is not None:
        result = result[-limit:]
    return result
