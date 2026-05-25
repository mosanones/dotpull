"""Dependency checking for dotpull — verify required tools are available."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DepResult:
    name: str
    required: bool
    found: bool
    path: Optional[str] = None
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.found or not self.required


@dataclass
class DepsReport:
    results: List[DepResult] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(r.ok for r in self.results)

    def summary(self) -> str:
        lines = []
        for r in self.results:
            status = "ok" if r.found else ("MISSING" if r.required else "optional, not found")
            path_info = f" ({r.path})" if r.path else ""
            note_info = f" — {r.note}" if r.note else ""
            lines.append(f"  [{status}] {r.name}{path_info}{note_info}")
        return "\n".join(lines)


_KNOWN_DEPS: List[dict] = [
    {"name": "git", "required": True, "note": "needed for remote push/pull"},
    {"name": "diff", "required": False, "note": "used for file diffing"},
    {"name": "gpg", "required": False, "note": "optional encryption backend"},
    {"name": "patch", "required": False, "note": "needed for patch apply"},
    {"name": "rsync", "required": False, "note": "optional fast sync backend"},
]


def check_dep(name: str, required: bool = True, note: str = "") -> DepResult:
    """Check whether a single executable is available on PATH."""
    found_path = shutil.which(name)
    return DepResult(
        name=name,
        required=required,
        found=found_path is not None,
        path=found_path,
        note=note,
    )


def check_all_deps(extra: Optional[List[dict]] = None) -> DepsReport:
    """Check all known dependencies and return a DepsReport."""
    deps = list(_KNOWN_DEPS)
    if extra:
        deps.extend(extra)
    report = DepsReport()
    for dep in deps:
        report.results.append(
            check_dep(dep["name"], dep.get("required", True), dep.get("note", ""))
        )
    return report
