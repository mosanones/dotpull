"""Promote a profile's resolved variables/files into another profile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from dotpull.profile import Profile


class PromoteError(Exception):
    """Raised when promotion fails."""


@dataclass
class PromoteResult:
    source: str
    target: str
    merged_files: List[str] = field(default_factory=list)
    merged_vars: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    skipped_vars: List[str] = field(default_factory=list)
    ok: bool = True
    error: Optional[str] = None

    def healthy(self) -> bool:
        return self.ok

    def summary(self) -> str:
        parts = [
            f"Promoted '{self.source}' -> '{self.target}'",
            f"  files merged:   {len(self.merged_files)}",
            f"  vars merged:    {len(self.merged_vars)}",
            f"  files skipped:  {len(self.skipped_files)}",
            f"  vars skipped:   {len(self.skipped_vars)}",
        ]
        if self.error:
            parts.append(f"  error: {self.error}")
        return "\n".join(parts)


def promote_profile(
    source: Profile,
    target: Profile,
    overwrite: bool = False,
) -> PromoteResult:
    """Merge source profile's files and variables into target profile.

    Args:
        source: Profile whose values are promoted.
        target: Profile that receives the promoted values.
        overwrite: If True, existing keys in target are overwritten.

    Returns:
        PromoteResult summarising what changed.
    """
    result = PromoteResult(source=source.name, target=target.name)

    # Promote files
    target_files: dict = dict(target.files)
    for src_path, dest_path in source.files.items():
        if src_path in target_files and not overwrite:
            result.skipped_files.append(src_path)
        else:
            target_files[src_path] = dest_path
            result.merged_files.append(src_path)
    target.files = target_files

    # Promote variables
    target_vars: dict = dict(target.variables)
    for key, value in source.variables.items():
        if key in target_vars and not overwrite:
            result.skipped_vars.append(key)
        else:
            target_vars[key] = value
            result.merged_vars.append(key)
    target.variables = target_vars

    return result
