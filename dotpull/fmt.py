"""Format profile files (YAML dotfile configs) for consistent style."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


class FmtError(Exception):
    pass


@dataclass
class FmtResult:
    path: Path
    changed: bool
    dry_run: bool = False

    @property
    def healthy(self) -> bool:
        return not self.changed or self.dry_run

    def summary(self) -> str:
        if self.dry_run and self.changed:
            return f"[dry-run] would reformat: {self.path}"
        if self.changed:
            return f"reformatted: {self.path}"
        return f"ok: {self.path}"


@dataclass
class FmtReport:
    results: List[FmtResult] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(r.healthy for r in self.results)

    def changed_files(self) -> List[Path]:
        return [r.path for r in self.results if r.changed]

    def summary(self) -> str:
        changed = self.changed_files()
        if not changed:
            return "All files already well-formatted."
        return f"{len(changed)} file(s) reformatted: " + ", ".join(str(p) for p in changed)


def _canonical_yaml(data: object) -> str:
    """Dump data to a canonical YAML string (sorted keys, 2-space indent)."""
    return yaml.dump(data, default_flow_style=False, sort_keys=True, indent=2, allow_unicode=True)


def fmt_file(path: Path, *, dry_run: bool = False) -> FmtResult:
    """Format a single YAML file in-place. Returns FmtResult indicating whether it changed."""
    if not path.exists():
        raise FmtError(f"File not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise FmtError(f"YAML parse error in {path}: {exc}") from exc
    if data is None:
        data = {}
    canonical = _canonical_yaml(data)
    changed = raw != canonical
    if changed and not dry_run:
        path.write_text(canonical, encoding="utf-8")
    return FmtResult(path=path, changed=changed, dry_run=dry_run)


def fmt_directory(directory: Path, *, dry_run: bool = False, glob: str = "**/*.yaml") -> FmtReport:
    """Format all YAML files under *directory* matching *glob*."""
    if not directory.is_dir():
        raise FmtError(f"Directory not found: {directory}")
    report = FmtReport()
    for yaml_path in sorted(directory.glob(glob)):
        result = fmt_file(yaml_path, dry_run=dry_run)
        report.results.append(result)
    return report
