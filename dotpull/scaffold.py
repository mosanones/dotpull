"""Scaffold new profile files from a template skeleton."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


class ScaffoldError(Exception):
    pass


@dataclass
class ScaffoldResult:
    profile_name: str
    created_files: List[Path] = field(default_factory=list)
    skipped_files: List[Path] = field(default_factory=list)
    dry_run: bool = False

    def healthy(self) -> bool:
        return len(self.created_files) > 0 or len(self.skipped_files) > 0

    def summary(self) -> str:
        action = "[dry-run] would create" if self.dry_run else "created"
        lines = [f"Scaffold '{self.profile_name}':"]
        for f in self.created_files:
            lines.append(f"  {action}: {f}")
        for f in self.skipped_files:
            lines.append(f"  skipped (exists): {f}")
        return "\n".join(lines)


_PROFILE_TEMPLATE = {
    "files": [],
    "variables": {},
    "extends": None,
}


def scaffold_profile(
    dotfiles_dir: Path,
    profile_name: str,
    sample_files: Optional[List[str]] = None,
    dry_run: bool = False,
) -> ScaffoldResult:
    """Create a skeleton profile entry and optional sample dotfiles."""
    profiles_path = dotfiles_dir / "profiles.yaml"
    if not profiles_path.exists():
        raise ScaffoldError(f"profiles.yaml not found in {dotfiles_dir}")

    with profiles_path.open() as fh:
        data = yaml.safe_load(fh) or {}

    result = ScaffoldResult(profile_name=profile_name, dry_run=dry_run)

    if profile_name in data:
        raise ScaffoldError(f"Profile '{profile_name}' already exists")

    entry = dict(_PROFILE_TEMPLATE)
    entry["files"] = sample_files or []

    if not dry_run:
        data[profile_name] = entry
        with profiles_path.open("w") as fh:
            yaml.dump(data, fh, default_flow_style=False, sort_keys=True)

    for rel in sample_files or []:
        dest = dotfiles_dir / rel
        if dest.exists():
            result.skipped_files.append(dest)
        else:
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(f"# {rel} — managed by dotpull\n")
            result.created_files.append(dest)

    return result
