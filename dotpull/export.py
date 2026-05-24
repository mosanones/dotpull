"""Export dotfiles profile to a portable archive."""

import tarfile
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotpull.profile import Profile


class ExportError(Exception):
    """Raised when an export operation fails."""


def _file_checksum(path: Path) -> str:
    """Return SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def export_profile(
    profile: Profile,
    dotfiles_dir: Path,
    output_path: Path,
    label: Optional[str] = None,
) -> Path:
    """Pack all files for *profile* into a .tar.gz archive.

    The archive contains:
    - Every resolved file listed in the profile (relative to dotfiles_dir).
    - A ``manifest.json`` at the archive root with metadata.

    Returns the path to the created archive.
    """
    if not dotfiles_dir.is_dir():
        raise ExportError(f"dotfiles directory not found: {dotfiles_dir}")

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"{profile.name}-{label or timestamp}.tar.gz"
    archive_path = output_path / archive_name
    output_path.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "profile": profile.name,
        "exported_at": timestamp,
        "label": label,
        "files": [],
    }

    with tarfile.open(archive_path, "w:gz") as tar:
        for rel in profile.files:
            src = dotfiles_dir / rel
            if not src.exists():
                raise ExportError(f"source file missing: {src}")
            checksum = _file_checksum(src)
            manifest["files"].append({"path": rel, "sha256": checksum})
            tar.add(src, arcname=rel)

        manifest_bytes = json.dumps(manifest, indent=2).encode()
        import io
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        tar.addfile(info, io.BytesIO(manifest_bytes))

    return archive_path


def import_archive(archive_path: Path, dotfiles_dir: Path) -> list[str]:
    """Extract an exported archive into *dotfiles_dir*.

    Returns a list of relative paths that were restored.
    """
    if not archive_path.exists():
        raise ExportError(f"archive not found: {archive_path}")

    dotfiles_dir.mkdir(parents=True, exist_ok=True)
    restored: list[str] = []

    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name == "manifest.json":
                continue
            tar.extract(member, path=dotfiles_dir)
            restored.append(member.name)

    return restored
