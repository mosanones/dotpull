"""Pin management: lock a profile's files to a specific snapshot revision."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PIN_FILE = ".dotpull_pins.json"


class PinError(Exception):
    """Raised when a pin operation fails."""


@dataclass
class PinEntry:
    profile: str
    snapshot: str
    created_at: str
    note: str = ""


@dataclass
class PinStore:
    pins: dict[str, PinEntry] = field(default_factory=dict)

    def get(self, profile: str) -> Optional[PinEntry]:
        return self.pins.get(profile)

    def set(self, entry: PinEntry) -> None:
        self.pins[entry.profile] = entry

    def remove(self, profile: str) -> bool:
        if profile in self.pins:
            del self.pins[profile]
            return True
        return False


def _pin_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / PIN_FILE


def load_pins(dotfiles_dir: Path) -> PinStore:
    path = _pin_path(dotfiles_dir)
    if not path.exists():
        return PinStore()
    data = json.loads(path.read_text())
    pins = {k: PinEntry(**v) for k, v in data.items()}
    return PinStore(pins=pins)


def save_pins(dotfiles_dir: Path, store: PinStore) -> None:
    path = _pin_path(dotfiles_dir)
    data = {k: vars(v) for k, v in store.pins.items()}
    path.write_text(json.dumps(data, indent=2))


def pin_profile(dotfiles_dir: Path, profile: str, snapshot: str, note: str = "") -> PinEntry:
    """Pin a profile to a specific snapshot."""
    from dotpull.snapshot import list_snapshots

    snapshots = list_snapshots(dotfiles_dir)
    names = [s["name"] for s in snapshots]
    if snapshot not in names:
        raise PinError(f"Snapshot '{snapshot}' not found. Available: {names}")

    from datetime import datetime, timezone
    entry = PinEntry(
        profile=profile,
        snapshot=snapshot,
        created_at=datetime.now(timezone.utc).isoformat(),
        note=note,
    )
    store = load_pins(dotfiles_dir)
    store.set(entry)
    save_pins(dotfiles_dir, store)
    return entry


def unpin_profile(dotfiles_dir: Path, profile: str) -> bool:
    """Remove a pin for a profile. Returns True if a pin was removed."""
    store = load_pins(dotfiles_dir)
    removed = store.remove(profile)
    if removed:
        save_pins(dotfiles_dir, store)
    return removed


def list_pins(dotfiles_dir: Path) -> list[PinEntry]:
    store = load_pins(dotfiles_dir)
    return list(store.pins.values())
