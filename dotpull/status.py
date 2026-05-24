"""Profile sync status reporting for dotpull."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotpull.diff import diff_profile_files, DiffResult
from dotpull.profile import Profile


@dataclass
class ProfileStatus:
    profile_name: str
    total: int = 0
    synced: int = 0
    missing: int = 0
    drifted: int = 0
    details: List[DiffResult] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.missing == 0 and self.drifted == 0

    def summary(self) -> str:
        parts = [f"profile={self.profile_name}", f"total={self.total}"]
        if self.synced:
            parts.append(f"synced={self.synced}")
        if self.missing:
            parts.append(f"missing={self.missing}")
        if self.drifted:
            parts.append(f"drifted={self.drifted}")
        return " ".join(parts)


def check_profile_status(
    profile: Profile,
    dotfiles_dir: Path,
    home_dir: Optional[Path] = None,
) -> ProfileStatus:
    """Return a ProfileStatus by diffing all files in *profile*."""
    if home_dir is None:
        home_dir = Path.home()

    results = diff_profile_files(profile, dotfiles_dir, home_dir)
    status = ProfileStatus(profile_name=profile.name, total=len(results), details=results)

    for r in results:
        if r.source_missing or r.target_missing:
            status.missing += 1
        elif r.content_differs or not r.is_symlink:
            status.drifted += 1
        else:
            status.synced += 1

    return status
