"""CLI commands for linting dotpull profiles."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.lint import lint_all, lint_profile
from dotpull.profile import Profile


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="lint")
def lint_group():
    """Lint profiles for errors and warnings."""


@lint_group.command(name="check")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--profile", "profile_name", default=None, help="Lint a single profile.")
@click.option("--strict", is_flag=True, help="Exit non-zero on warnings too.")
def cmd_check(config: str, profile_name: str | None, strict: bool):
    """Check profiles for lint issues."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"]).expanduser()
    raw_profiles: dict = cfg.get("profiles", {})

    profiles: dict[str, Profile] = {
        name: Profile(name=name, data=data, all_profiles=raw_profiles)
        for name, data in raw_profiles.items()
    }

    if profile_name:
        if profile_name not in profiles:
            click.echo(f"Unknown profile: {profile_name}", err=True)
            raise SystemExit(1)
        from dotpull.lint import lint_profile as _lp
        report = _lp(profiles[profile_name], dotfiles_dir)
    else:
        report = lint_all(profiles, dotfiles_dir)

    if not report.issues:
        click.echo("No issues found.")
        return

    for issue in report.issues:
        click.echo(str(issue))

    click.echo(f"\nSummary: {report.summary}")

    if not report.healthy or (strict and report.issues):
        raise SystemExit(1)
