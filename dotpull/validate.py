"""Profile file validation — check dotfile sources exist and targets are sane."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotpull.profile import Profile


@dataclass
class ValidationIssue:
    file: str
    reason: str
    severity: str  # "error" | "warning"


@dataclass
class ValidationReport:
    profile_name: str
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def summary(self) -> str:
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        if not self.issues:
            return f"Profile '{self.profile_name}': all files OK"
        return (
            f"Profile '{self.profile_name}': {errors} error(s), {warnings} warning(s)"
        )


def validate_profile_files(
    profile: Profile,
    dotfiles_dir: Path,
) -> ValidationReport:
    """Validate that all files declared in *profile* are consistent.

    Checks performed:
    - Source file exists inside *dotfiles_dir*.
    - Target path is not empty.
    - Target path is not an absolute path pointing outside HOME (warning only).
    """
    report = ValidationReport(profile_name=profile.name)

    for entry in profile.files:
        src_rel = entry.get("src", "")
        target = entry.get("target", "")

        if not src_rel:
            report.issues.append(
                ValidationIssue(file="(unknown)", reason="Missing 'src' key", severity="error")
            )
            continue

        source_path = dotfiles_dir / src_rel

        if not source_path.exists():
            report.issues.append(
                ValidationIssue(
                    file=src_rel,
                    reason=f"Source file not found: {source_path}",
                    severity="error",
                )
            )

        if not target:
            report.issues.append(
                ValidationIssue(
                    file=src_rel,
                    reason="Missing or empty 'target' key",
                    severity="error",
                )
            )
        elif Path(target).is_absolute():
            report.issues.append(
                ValidationIssue(
                    file=src_rel,
                    reason=f"Target is an absolute path: {target}",
                    severity="warning",
                )
            )

    return report
