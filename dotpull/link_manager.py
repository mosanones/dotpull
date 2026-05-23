"""High-level link manager that wires together profiles, config, and symlinks."""

from pathlib import Path
from typing import Any

from dotpull.link import audit_link, create_link, remove_link, LinkError
from dotpull.profile import Profile


class LinkManager:
    """Applies and tears down symlinks for a resolved profile."""

    def __init__(self, dotfiles_dir: Path, home_dir: Path | None = None) -> None:
        self.dotfiles_dir = dotfiles_dir
        self.home_dir = home_dir or Path.home()

    def apply(self, profile: Profile, force: bool = False) -> list[dict[str, Any]]:
        """Create symlinks for every file declared in *profile*.

        Returns a list of result dicts with keys: source, target, status, error.
        """
        results = []
        for rel_path in profile.files:
            source = self.dotfiles_dir / rel_path
            target = self.home_dir / rel_path
            try:
                create_link(source, target, force=force)
                results.append({"source": source, "target": target, "status": "linked", "error": None})
            except LinkError as exc:
                results.append({"source": source, "target": target, "status": "error", "error": str(exc)})
        return results

    def remove(self, profile: Profile) -> list[dict[str, Any]]:
        """Remove symlinks for every file declared in *profile*.

        Returns a list of result dicts with keys: target, removed.
        """
        results = []
        for rel_path in profile.files:
            target = self.home_dir / rel_path
            removed = remove_link(target)
            results.append({"target": target, "removed": removed})
        return results

    def audit(self, profile: Profile) -> list[dict[str, Any]]:
        """Audit symlinks for every file declared in *profile*.

        Returns a list of result dicts with keys: source, target, status.
        """
        results = []
        for rel_path in profile.files:
            source = self.dotfiles_dir / rel_path
            target = self.home_dir / rel_path
            status = audit_link(source, target)
            results.append({"source": source, "target": target, "status": status})
        return results
