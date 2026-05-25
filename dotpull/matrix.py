"""Matrix: compare a profile's resolved variables across multiple environments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from dotpull.resolve import resolve_variables


@dataclass
class MatrixRow:
    profile: str
    environment: str
    variables: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> Optional[str]:
        return self.variables.get(key)


@dataclass
class MatrixReport:
    rows: List[MatrixRow] = field(default_factory=list)
    keys: List[str] = field(default_factory=list)

    def healthy(self) -> bool:
        """True when every environment resolves the same value for every key."""
        if not self.keys or not self.rows:
            return True
        for key in self.keys:
            values = {row.get(key) for row in self.rows}
            if len(values) > 1:
                return False
        return True

    def differing_keys(self) -> List[str]:
        """Return keys whose value differs across at least two environments."""
        differing = []
        for key in self.keys:
            values = {row.get(key) for row in self.rows}
            if len(values) > 1:
                differing.append(key)
        return differing

    def summary(self) -> str:
        diff = self.differing_keys()
        if not diff:
            return "All environments agree on every variable."
        return f"{len(diff)} variable(s) differ across environments: {', '.join(diff)}"


def build_matrix(
    profile_name: str,
    profiles: Dict[str, object],
    environments: Dict[str, Dict[str, str]],
    config_vars: Optional[Dict[str, str]] = None,
) -> MatrixReport:
    """Build a MatrixReport by resolving *profile_name* under each environment.

    Args:
        profile_name: Name of the profile to inspect.
        profiles: Mapping of profile name -> Profile object.
        environments: Mapping of environment label -> env-var overrides dict.
        config_vars: Global config-level variables (lowest priority).
    """
    if profile_name not in profiles:
        raise KeyError(f"Unknown profile: {profile_name!r}")

    config_vars = config_vars or {}
    report = MatrixReport()
    all_keys: set = set()

    for env_label, env_overrides in environments.items():
        resolved = resolve_variables(
            profile_name=profile_name,
            profiles=profiles,
            config_vars=config_vars,
            env_overrides=env_overrides,
        )
        row = MatrixRow(
            profile=profile_name,
            environment=env_label,
            variables=resolved.as_dict(),
        )
        report.rows.append(row)
        all_keys.update(resolved.as_dict().keys())

    report.keys = sorted(all_keys)
    return report
