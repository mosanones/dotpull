"""Compare two profiles side-by-side: files, variables, and overrides."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from dotpull.profile import Profile


@dataclass
class CompareResult:
    profile_a: str
    profile_b: str
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    in_both: List[str] = field(default_factory=list)
    vars_only_in_a: Dict[str, str] = field(default_factory=dict)
    vars_only_in_b: Dict[str, str] = field(default_factory=dict)
    vars_differ: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, val_a, val_b)
    vars_same: Dict[str, str] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return bool(
            self.only_in_a
            or self.only_in_b
            or self.vars_only_in_a
            or self.vars_only_in_b
            or self.vars_differ
        )

    def summary(self) -> str:
        lines = [f"Compare: {self.profile_a!r} vs {self.profile_b!r}"]
        if self.only_in_a:
            lines.append(f"  Files only in {self.profile_a}: {', '.join(self.only_in_a)}")
        if self.only_in_b:
            lines.append(f"  Files only in {self.profile_b}: {', '.join(self.only_in_b)}")
        if self.in_both:
            lines.append(f"  Files in both: {', '.join(self.in_both)}")
        for key, va, vb in self.vars_differ:
            lines.append(f"  Var {key!r}: {va!r} -> {vb!r}")
        if not self.has_differences:
            lines.append("  Profiles are identical.")
        return "\n".join(lines)


def compare_profiles(profile_a: Profile, profile_b: Profile) -> CompareResult:
    """Return a CompareResult describing differences between two resolved profiles."""
    files_a: Set[str] = set(profile_a.files)
    files_b: Set[str] = set(profile_b.files)

    result = CompareResult(
        profile_a=profile_a.name,
        profile_b=profile_b.name,
        only_in_a=sorted(files_a - files_b),
        only_in_b=sorted(files_b - files_a),
        in_both=sorted(files_a & files_b),
    )

    vars_a: Dict[str, str] = dict(profile_a.variables)
    vars_b: Dict[str, str] = dict(profile_b.variables)
    all_keys = set(vars_a) | set(vars_b)

    for key in sorted(all_keys):
        if key in vars_a and key not in vars_b:
            result.vars_only_in_a[key] = vars_a[key]
        elif key in vars_b and key not in vars_a:
            result.vars_only_in_b[key] = vars_b[key]
        elif vars_a[key] != vars_b[key]:
            result.vars_differ.append((key, vars_a[key], vars_b[key]))
        else:
            result.vars_same[key] = vars_a[key]

    return result
