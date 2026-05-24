"""Schedule periodic sync operations for profiles."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional


class ScheduleError(Exception):
    pass


@dataclass
class ScheduleEntry:
    profile: str
    interval_seconds: int
    last_run: Optional[float] = None
    enabled: bool = True


@dataclass
class ScheduleStore:
    entries: dict[str, ScheduleEntry] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "ScheduleStore":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        entries = {
            k: ScheduleEntry(**v) for k, v in data.get("entries", {}).items()
        }
        return cls(entries=entries)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"entries": {k: asdict(v) for k, v in self.entries.items()}}
        path.write_text(json.dumps(data, indent=2))

    def add(self, profile: str, interval_seconds: int) -> ScheduleEntry:
        if interval_seconds <= 0:
            raise ScheduleError("interval_seconds must be positive")
        entry = ScheduleEntry(profile=profile, interval_seconds=interval_seconds)
        self.entries[profile] = entry
        return entry

    def remove(self, profile: str) -> None:
        if profile not in self.entries:
            raise ScheduleError(f"No schedule found for profile '{profile}'")
        del self.entries[profile]

    def due(self, now: Optional[float] = None) -> list[ScheduleEntry]:
        now = now or time.time()
        result = []
        for entry in self.entries.values():
            if not entry.enabled:
                continue
            if entry.last_run is None or (now - entry.last_run) >= entry.interval_seconds:
                result.append(entry)
        return result

    def mark_run(self, profile: str, now: Optional[float] = None) -> None:
        if profile not in self.entries:
            raise ScheduleError(f"No schedule found for profile '{profile}'")
        self.entries[profile].last_run = now or time.time()


def run_due(
    store: ScheduleStore,
    on_sync: Callable[[str], None],
    now: Optional[float] = None,
) -> list[str]:
    """Run on_sync for each due profile and record run times."""
    now = now or time.time()
    ran = []
    for entry in store.due(now=now):
        on_sync(entry.profile)
        store.mark_run(entry.profile, now=now)
        ran.append(entry.profile)
    return ran
