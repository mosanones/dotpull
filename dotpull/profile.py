"""Profile resolution and management for dotpull."""

from pathlib import Path
from typing import Any


class Profile:
    """Represents a dotpull profile with its file mappings and overrides."""

    def __init__(self, name: str, data: dict[str, Any], dotfiles_dir: Path):
        self.name = name
        self.dotfiles_dir = dotfiles_dir
        self._data = data or {}

    @property
    def files(self) -> dict[str, str]:
        """Return file mappings: source (relative to dotfiles_dir) -> target (absolute)."""
        return self._data.get("files", {})

    @property
    def extends(self) -> str | None:
        """Return the name of the parent profile this one extends, if any."""
        return self._data.get("extends")

    @property
    def variables(self) -> dict[str, str]:
        """Return profile-specific variables for template substitution."""
        return self._data.get("variables", {})

    def resolve_files(self) -> dict[Path, Path]:
        """Resolve file mappings to absolute Paths."""
        resolved = {}
        for src, dst in self.files.items():
            source = self.dotfiles_dir / src
            target = Path(dst).expanduser()
            resolved[source] = target
        return resolved


def resolve_profile(name: str, config: dict[str, Any], _seen: set[str] | None = None) -> Profile:
    """Resolve a profile by name, merging with any parent profiles.

    Args:
        name: The profile name to resolve.
        config: The full dotpull configuration dictionary.
        _seen: Internal set used to detect circular inheritance chains.

    Raises:
        ValueError: If the profile is not found or a circular extends chain is detected.
    """
    if _seen is None:
        _seen = set()

    if name in _seen:
        chain = " -> ".join(sorted(_seen)) + f" -> {name}"
        raise ValueError(f"Circular profile inheritance detected: {chain}")

    _seen.add(name)

    dotfiles_dir = Path(config["dotfiles_dir"])
    profiles_data = config.get("profiles", {})

    if name not in profiles_data and name != "default":
        raise ValueError(f"Profile '{name}' not found in configuration")

    raw = profiles_data.get(name, {})
    profile = Profile(name, raw, dotfiles_dir)

    if profile.extends:
        parent = resolve_profile(profile.extends, config, _seen)
        merged_files = {**parent.files, **profile.files}
        merged_vars = {**parent.variables, **profile.variables}
        merged_data = {**raw, "files": merged_files, "variables": merged_vars}
        profile = Profile(name, merged_data, dotfiles_dir)

    return profile
