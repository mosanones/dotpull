"""Initialize a new dotpull-managed dotfiles directory."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml

DEFAULT_CONFIG = {
    "dotfiles_dir": "~/dotfiles",
    "backup_dir": "~/.dotpull/backups",
    "default_profile": "default",
    "variables": {},
}

DEFAULT_PROFILE = {
    "default": {
        "files": [],
        "variables": {},
    }
}


@dataclass
class InitResult:
    created: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def init_dotfiles_dir(
    target: str | os.PathLike = "~/dotfiles",
    force: bool = False,
) -> InitResult:
    """Scaffold a new dotfiles directory with default config and profile."""
    result = InitResult()
    root = Path(target).expanduser().resolve()

    dirs_to_create = [
        root,
        root / ".dotpull" / "snapshots",
        root / ".dotpull" / "backups",
    ]
    for d in dirs_to_create:
        if d.exists():
            result.skipped.append(str(d))
        else:
            try:
                d.mkdir(parents=True, exist_ok=True)
                result.created.append(str(d))
            except OSError as exc:
                result.errors.append(f"Cannot create {d}: {exc}")
                return result

    config_path = root / "dotpull.yaml"
    _write_yaml(config_path, DEFAULT_CONFIG, force, result)

    profiles_path = root / "profiles.yaml"
    _write_yaml(profiles_path, DEFAULT_PROFILE, force, result)

    gitignore_path = root / ".gitignore"
    _write_text(gitignore_path, ".dotpull/backups/\n", force, result)

    return result


def _write_yaml(
    path: Path, data: dict, force: bool, result: InitResult
) -> None:
    if path.exists() and not force:
        result.skipped.append(str(path))
        return
    try:
        path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
        result.created.append(str(path))
    except OSError as exc:
        result.errors.append(f"Cannot write {path}: {exc}")


def _write_text(
    path: Path, text: str, force: bool, result: InitResult
) -> None:
    if path.exists() and not force:
        result.skipped.append(str(path))
        return
    try:
        path.write_text(text, encoding="utf-8")
        result.created.append(str(path))
    except OSError as exc:
        result.errors.append(f"Cannot write {path}: {exc}")
