"""Snapshot management: capture and restore dotfile states."""

import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

SNAPSHOT_DIR_NAME = ".dotpull_snapshots"


class SnapshotError(Exception):
    pass


def _snapshot_dir(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / SNAPSHOT_DIR_NAME


def _file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def create_snapshot(dotfiles_dir: Path, label: str = "") -> Path:
    """Capture current state of all tracked dotfiles into a timestamped snapshot."""
    snap_dir = _snapshot_dir(dotfiles_dir)
    snap_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    name = f"{timestamp}_{label}" if label else timestamp
    snap_path = snap_dir / name
    snap_path.mkdir()

    manifest = {"label": label, "timestamp": timestamp, "files": {}}

    for src in dotfiles_dir.rglob("*"):
        if src.is_file() and SNAPSHOT_DIR_NAME not in src.parts:
            rel = src.relative_to(dotfiles_dir)
            dest = snap_path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            manifest["files"][str(rel)] = _file_checksum(src)

    (snap_path / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return snap_path


def list_snapshots(dotfiles_dir: Path) -> list[dict]:
    """Return metadata for all available snapshots, newest first."""
    snap_dir = _snapshot_dir(dotfiles_dir)
    if not snap_dir.exists():
        return []

    results = []
    for entry in sorted(snap_dir.iterdir(), reverse=True):
        manifest_path = entry / "manifest.json"
        if entry.is_dir() and manifest_path.exists():
            data = json.loads(manifest_path.read_text())
            data["name"] = entry.name
            results.append(data)
    return results


def restore_snapshot(dotfiles_dir: Path, snapshot_name: str) -> list[str]:
    """Restore dotfiles from a named snapshot. Returns list of restored file paths."""
    snap_path = _snapshot_dir(dotfiles_dir) / snapshot_name
    if not snap_path.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_name}")

    manifest_path = snap_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    restored = []

    for rel_str in manifest["files"]:
        src = snap_path / rel_str
        dest = dotfiles_dir / rel_str
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        restored.append(rel_str)

    return restored
