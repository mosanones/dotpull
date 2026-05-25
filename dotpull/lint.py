"""Lint profiles and config for common mistakes and best practices."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotpull.profile import Profile


@dataclass
class LintIssue:
    level: str  # "error" | "warning" | "info"
    profile: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.profile}: {self.message}"


@dataclass
class LintReport:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    @property
    def summary(self) -> str:
        errors = sum(1 for i in self.issues if i.level == "error")
        warnings = sum(1 for i in self.issues if i.level == "warning")
        return f"{errors} error(s), {warnings} warning(s)"

    def add(self, level: str, profile: str, message: str) -> None:
        self.issues.append(LintIssue(level=level, profile=profile, message=message))


def lint_profile(profile: Profile, dotfiles_dir: Path) -> LintReport:
    """Run lint checks against a single resolved profile."""
    report = LintReport()
    name = profile.name

    if not profile.files:
        report.add("warning", name, "profile defines no files")

    seen_targets: dict[str, str] = {}
    for src, tgt in profile.files.items():
        source_path = dotfiles_dir / src
        if not source_path.exists():
            report.add("error", name, f"source file not found: {src}")

        if tgt in seen_targets:
            report.add(
                "error",
                name,
                f"duplicate target '{tgt}' for sources '{seen_targets[tgt]}' and '{src}'",
            )
        else:
            seen_targets[tgt] = src

        if not tgt.startswith(("~/", "/")):
            report.add("warning", name, f"target path may be relative: {tgt}")

    for var_name, var_value in (profile.variables or {}).items():
        if not var_name.strip():
            report.add("error", name, "variable with empty name found")
        if var_value is None:
            report.add("warning", name, f"variable '{var_name}' has null value")

    return report


def lint_all(profiles: dict[str, Profile], dotfiles_dir: Path) -> LintReport:
    """Lint all profiles and merge results into one report."""
    combined = LintReport()
    for profile in profiles.values():
        sub = lint_profile(profile, dotfiles_dir)
        combined.issues.extend(sub.issues)
    return combined
