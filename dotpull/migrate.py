"""Profile migration: rename, copy, or transform profile definitions."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class MigrateError(Exception):
    """Raised when a migration operation fails."""


@dataclass
class MigrateResult:
    success: bool
    source: str
    destination: str
    message: str = ""


def _load_profiles(profiles_path: Path) -> dict[str, Any]:
    if not profiles_path.exists():
        raise MigrateError(f"Profiles file not found: {profiles_path}")
    with profiles_path.open() as fh:
        data = yaml.safe_load(fh) or {}
    return data


def _save_profiles(profiles_path: Path, data: dict[str, Any]) -> None:
    with profiles_path.open("w") as fh:
        yaml.safe_dump(data, fh, default_flow_style=False)


def rename_profile(
    profiles_path: Path,
    source: str,
    destination: str,
    *,
    overwrite: bool = False,
) -> MigrateResult:
    """Rename *source* profile to *destination* inside profiles.yaml."""
    data = _load_profiles(profiles_path)
    profiles: dict[str, Any] = data.get("profiles", {})

    if source not in profiles:
        raise MigrateError(f"Source profile '{source}' does not exist.")
    if destination in profiles and not overwrite:
        raise MigrateError(
            f"Destination profile '{destination}' already exists. Use overwrite=True."
        )

    profiles[destination] = profiles.pop(source)

    # Fix any 'extends' references pointing to source
    for name, body in profiles.items():
        if isinstance(body, dict) and body.get("extends") == source:
            body["extends"] = destination

    data["profiles"] = profiles
    _save_profiles(profiles_path, data)
    return MigrateResult(True, source, destination, f"Renamed '{source}' -> '{destination}'.")


def copy_profile(
    profiles_path: Path,
    source: str,
    destination: str,
    *,
    overwrite: bool = False,
) -> MigrateResult:
    """Copy *source* profile to *destination* without removing the original."""
    import copy

    data = _load_profiles(profiles_path)
    profiles: dict[str, Any] = data.get("profiles", {})

    if source not in profiles:
        raise MigrateError(f"Source profile '{source}' does not exist.")
    if destination in profiles and not overwrite:
        raise MigrateError(
            f"Destination profile '{destination}' already exists. Use overwrite=True."
        )

    profiles[destination] = copy.deepcopy(profiles[source])
    data["profiles"] = profiles
    _save_profiles(profiles_path, data)
    return MigrateResult(True, source, destination, f"Copied '{source}' -> '{destination}'.")
