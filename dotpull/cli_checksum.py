"""CLI commands for checksum management."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from dotpull.checksum import (
    ChecksumError,
    compute_checksums,
    save_checksums,
    verify_checksums,
    load_checksums,
)
from dotpull.config import load_config, validate_config
from dotpull.profile import Profile


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="checksum")
def checksum_group():
    """Verify and record file checksums."""


@checksum_group.command("record")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--profile", "profile_name", default="default", show_default=True)
def cmd_record(config: str, profile_name: str):
    """Compute and save checksums for the given profile's files."""
    cfg = _load(config)
    profiles = cfg.get("profiles", {})
    if profile_name not in profiles:
        click.echo(f"Unknown profile: {profile_name}", err=True)
        sys.exit(1)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    p = Profile(profile_name, profiles[profile_name], profiles)
    files = [entry["src"] for entry in p.files()]
    try:
        entries = compute_checksums(dotfiles_dir, files)
        save_checksums(dotfiles_dir, entries)
        click.echo(f"Recorded checksums for {len(entries)} file(s).")
    except ChecksumError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@checksum_group.command("verify")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--profile", "profile_name", default="default", show_default=True)
def cmd_verify(config: str, profile_name: str):
    """Verify current files against stored checksums."""
    cfg = _load(config)
    profiles = cfg.get("profiles", {})
    if profile_name not in profiles:
        click.echo(f"Unknown profile: {profile_name}", err=True)
        sys.exit(1)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    p = Profile(profile_name, profiles[profile_name], profiles)
    files = [entry["src"] for entry in p.files()]
    report = verify_checksums(dotfiles_dir, files)
    click.echo(report.summary())
    if not report.healthy():
        for m in report.mismatches:
            click.echo(f"  MISMATCH: {m}")
        sys.exit(1)


@checksum_group.command("list")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_list(config: str):
    """List all stored checksums."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    stored = load_checksums(dotfiles_dir)
    if not stored:
        click.echo("No checksums recorded.")
        return
    for path, sha in stored.items():
        click.echo(f"{sha[:12]}  {path}")
