"""Audit dotfile links and report their status across a profile."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotpull.link import audit_link, LinkError
from dotpull.profile import Profile


@dataclass
class AuditEntry:
    source: Path
    target: Path
    status: str  # 'ok', 'missing_source', 'missing_target', 'conflict', 'wrong_target'
    detail: Optional[str] = None


@dataclass
class AuditReport:
    profile_name: str
    entries: List[AuditEntry] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(e.status == "ok" for e in self.entries)

    @property
    def issues(self) -> List[AuditEntry]:
        return [e for e in self.entries if e.status != "ok"]

    def summary(self) -> str:
        total = len(self.entries)
        ok = sum(1 for e in self.entries if e.status == "ok")
        return f"{ok}/{total} links healthy for profile '{self.profile_name}'"


def audit_profile(
    profile: Profile,
    dotfiles_dir: Path,
    home_dir: Optional[Path] = None,
) -> AuditReport:
    """Audit all managed links for the given profile."""
    if home_dir is None:
        home_dir = Path.home()

    report = AuditReport(profile_name=profile.name)

    resolved = profile.resolve_files()
    for rel_path, target_path in resolved.items():
        source = dotfiles_dir / rel_path
        target = home_dir / target_path if not Path(target_path).is_absolute() else Path(target_path)

        try:
            result = audit_link(source, target)
            report.entries.append(
                AuditEntry(
                    source=source,
                    target=target,
                    status=result.status,
                    detail=result.detail,
                )
            )
        except LinkError as exc:
            report.entries.append(
                AuditEntry(
                    source=source,
                    target=target,
                    status="error",
                    detail=str(exc),
                )
            )

    return report
