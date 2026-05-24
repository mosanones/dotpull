"""Health-check utilities for a dotpull environment."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotpull.config import load_config, validate_config
from dotpull.link import audit_link
from dotpull.profile import Profile


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str


@dataclass
class DoctorReport:
    results: List[CheckResult] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(r.ok for r in self.results)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)


def _check_config(config_path: Path) -> CheckResult:
    try:
        cfg = load_config(config_path)
        validate_config(cfg)
        return CheckResult("config", True, f"Config valid at {config_path}")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("config", False, str(exc))


def _check_dotfiles_dir(cfg: dict) -> CheckResult:
    d = Path(cfg.get("dotfiles_dir", ""))
    if d.is_dir():
        return CheckResult("dotfiles_dir", True, f"{d} exists")
    return CheckResult("dotfiles_dir", False, f"dotfiles_dir '{d}' not found")


def _check_symlinks(profile: Profile, home_dir: Path) -> List[CheckResult]:
    results = []
    for rel in profile.files:
        src = Path(profile._dotfiles_dir) / rel  # type: ignore[attr-defined]
        target = home_dir / rel
        status = audit_link(src, target)
        ok = status == "ok"
        results.append(CheckResult(f"link:{rel}", ok, f"{rel}: {status}"))
    return results


def run_doctor(
    config_path: Path,
    profile_name: str | None = None,
    home_dir: Path | None = None,
) -> DoctorReport:
    report = DoctorReport()

    cfg_check = _check_config(config_path)
    report.add(cfg_check)
    if not cfg_check.ok:
        return report

    cfg = load_config(config_path)
    report.add(_check_dotfiles_dir(cfg))

    name = profile_name or cfg.get("default_profile", "default")
    profiles_raw = cfg.get("profiles", {})
    if name not in profiles_raw:
        report.add(CheckResult("profile", False, f"Profile '{name}' not defined"))
        return report
    report.add(CheckResult("profile", True, f"Profile '{name}' found"))

    dotfiles_dir = Path(cfg["dotfiles_dir"])
    profile = Profile(name, profiles_raw, dotfiles_dir)
    hd = home_dir or Path(os.path.expanduser("~"))
    for r in _check_symlinks(profile, hd):
        report.add(r)

    return report
