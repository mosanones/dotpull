"""Remote repository sync support for dotpull."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class RemoteError(Exception):
    """Raised when a remote operation fails."""


@dataclass
class RemoteResult:
    success: bool
    message: str
    output: str = ""
    errors: List[str] = field(default_factory=list)


def _run(cmd: List[str], cwd: Path) -> tuple[int, str, str]:
    """Run a subprocess command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_git_repo(dotfiles_dir: Path) -> bool:
    """Return True if dotfiles_dir is inside a git repository."""
    code, _, _ = _run(["git", "rev-parse", "--git-dir"], dotfiles_dir)
    return code == 0


def remote_push(dotfiles_dir: Path, message: Optional[str] = None) -> RemoteResult:
    """Stage all changes, commit, and push to the configured remote."""
    if not is_git_repo(dotfiles_dir):
        raise RemoteError(f"{dotfiles_dir} is not a git repository")

    commit_msg = message or "dotpull: sync dotfiles"

    code, out, err = _run(["git", "add", "-A"], dotfiles_dir)
    if code != 0:
        return RemoteResult(success=False, message="git add failed", output=out, errors=[err])

    code, out, err = _run(["git", "commit", "-m", commit_msg], dotfiles_dir)
    if code != 0 and "nothing to commit" not in out + err:
        return RemoteResult(success=False, message="git commit failed", output=out, errors=[err])

    code, out, err = _run(["git", "push"], dotfiles_dir)
    if code != 0:
        return RemoteResult(success=False, message="git push failed", output=out, errors=[err])

    return RemoteResult(success=True, message="Pushed successfully", output=out)


def remote_pull(dotfiles_dir: Path) -> RemoteResult:
    """Pull latest changes from the configured remote."""
    if not is_git_repo(dotfiles_dir):
        raise RemoteError(f"{dotfiles_dir} is not a git repository")

    code, out, err = _run(["git", "pull", "--ff-only"], dotfiles_dir)
    if code != 0:
        return RemoteResult(success=False, message="git pull failed", output=out, errors=[err])

    return RemoteResult(success=True, message="Pulled successfully", output=out)


def remote_status(dotfiles_dir: Path) -> RemoteResult:
    """Return the git status of the dotfiles directory."""
    if not is_git_repo(dotfiles_dir):
        raise RemoteError(f"{dotfiles_dir} is not a git repository")

    code, out, err = _run(["git", "status", "--short"], dotfiles_dir)
    if code != 0:
        return RemoteResult(success=False, message="git status failed", output=out, errors=[err])

    return RemoteResult(success=True, message="Status retrieved", output=out)
