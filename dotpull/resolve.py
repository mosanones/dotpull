"""Variable resolution: merge config, profile, and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from dotpull.profile import Profile


class ResolveError(Exception):
    """Raised when variable resolution fails."""


@dataclass
class ResolvedVars:
    """Holds the fully resolved variable set for a profile."""

    profile_name: str
    variables: Dict[str, str] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)  # var -> where it came from

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.variables.get(key, default)


def resolve_variables(
    profile: Profile,
    config: dict,
    *,
    include_env: bool = False,
    env_prefix: str = "DOTPULL_",
) -> ResolvedVars:
    """Resolve variables for *profile* by merging layers in priority order.

    Priority (highest → lowest):
      1. Environment variables (if *include_env* is True)
      2. Profile-level variables
      3. Parent profile variables (via ``extends``)
      4. Global ``variables`` block in config
    """
    result = ResolvedVars(profile_name=profile.name)

    # Layer 1 – global config variables (lowest priority)
    for k, v in config.get("variables", {}).items():
        result.variables[k] = str(v)
        result.sources[k] = "config"

    # Layer 2 – parent profile variables
    parent_name = profile.extends
    if parent_name:
        parent_vars = config.get("profiles", {}).get(parent_name, {}).get("variables", {})
        for k, v in parent_vars.items():
            result.variables[k] = str(v)
            result.sources[k] = f"profile:{parent_name}"

    # Layer 3 – current profile variables
    for k, v in profile.variables.items():
        result.variables[k] = str(v)
        result.sources[k] = f"profile:{profile.name}"

    # Layer 4 – environment variables (highest priority)
    if include_env:
        for env_key, env_val in os.environ.items():
            if env_key.startswith(env_prefix):
                var_name = env_key[len(env_prefix):].lower()
                result.variables[var_name] = env_val
                result.sources[var_name] = f"env:{env_key}"

    return result
