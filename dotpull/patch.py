"""Apply and track patch-based overrides to dotfiles."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class PatchError(Exception):
    """Raised when a patch operation fails."""


@dataclass
class PatchResult:
    success: bool
    patched: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def healthy(self) -> bool:
        return self.success and not self.errors

    def summary(self) -> str:
        parts = [f"patched={len(self.patched)}", f"skipped={len(self.skipped)}"]
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        return ", ".join(parts)


def _patch_dir(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".patches"


def apply_patch(source: Path, patch_file: Path, dry_run: bool = False) -> bool:
    """Apply a unified diff patch to source. Returns True if applied cleanly."""
    if not source.exists():
        raise PatchError(f"Source file not found: {source}")
    if not patch_file.exists():
        raise PatchError(f"Patch file not found: {patch_file}")
    cmd = ["patch", "--dry-run" if dry_run else "-N", str(source), str(patch_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def apply_patches_for_profile(
    profile_name: str,
    dotfiles_dir: Path,
    target_files: List[Path],
    dry_run: bool = False,
) -> PatchResult:
    """Apply all patches registered for a profile to the matching target files."""
    patch_root = _patch_dir(dotfiles_dir) / profile_name
    if not patch_root.exists():
        return PatchResult(success=True, skipped=[str(f) for f in target_files])

    patched: List[str] = []
    skipped: List[str] = []
    errors: List[str] = []

    for target in target_files:
        patch_file = patch_root / (target.name + ".patch")
        if not patch_file.exists():
            skipped.append(str(target))
            continue
        try:
            ok = apply_patch(target, patch_file, dry_run=dry_run)
            if ok:
                patched.append(str(target))
            else:
                errors.append(f"Patch did not apply cleanly: {patch_file}")
        except PatchError as exc:
            errors.append(str(exc))

    return PatchResult(
        success=len(errors) == 0,
        patched=patched,
        skipped=skipped,
        errors=errors,
    )


def list_patches(dotfiles_dir: Path, profile_name: Optional[str] = None) -> List[Path]:
    """List available patch files, optionally filtered by profile."""
    patch_root = _patch_dir(dotfiles_dir)
    if not patch_root.exists():
        return []
    if profile_name:
        return sorted((patch_root / profile_name).glob("*.patch"))
    return sorted(patch_root.rglob("*.patch"))
