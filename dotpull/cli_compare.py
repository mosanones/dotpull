"""CLI commands for comparing two dotpull profiles."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.profile import Profile
from dotpull.compare import compare_profiles


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    issues = validate_config(cfg)
    if issues:
        click.echo("Config errors: " + "; ".join(issues), err=True)
        sys.exit(1)
    return cfg


@click.group(name="compare")
def compare_group():
    """Compare two profiles side-by-side."""


@compare_group.command("show")
@click.argument("profile_a")
@click.argument("profile_b")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--files-only", is_flag=True, default=False, help="Only compare file lists.")
@click.option("--vars-only", is_flag=True, default=False, help="Only compare variables.")
def cmd_show(profile_a: str, profile_b: str, config: str, files_only: bool, vars_only: bool):
    """Show differences between PROFILE_A and PROFILE_B."""
    cfg = _load(config)
    profiles: dict = cfg.get("profiles", {})

    for name in (profile_a, profile_b):
        if name not in profiles:
            click.echo(f"Unknown profile: {name!r}", err=True)
            sys.exit(1)

    pa = Profile(profile_a, profiles, cfg)
    pb = Profile(profile_b, profiles, cfg)
    result = compare_profiles(pa, pb)

    if files_only:
        if result.only_in_a:
            click.echo(f"Only in {profile_a}: " + ", ".join(result.only_in_a))
        if result.only_in_b:
            click.echo(f"Only in {profile_b}: " + ", ".join(result.only_in_b))
        if result.in_both:
            click.echo("In both: " + ", ".join(result.in_both))
    elif vars_only:
        for key, val in result.vars_only_in_a.items():
            click.echo(f"[{profile_a} only] {key}={val}")
        for key, val in result.vars_only_in_b.items():
            click.echo(f"[{profile_b} only] {key}={val}")
        for key, va, vb in result.vars_differ:
            click.echo(f"[differ] {key}: {va!r} -> {vb!r}")
    else:
        click.echo(result.summary())

    sys.exit(0 if not result.has_differences else 1)
