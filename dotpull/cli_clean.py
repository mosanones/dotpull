"""CLI commands for cleaning stale dotpull artefacts."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.clean import clean_broken_symlinks, clean_stale_links
from dotpull.config import load_config, validate_config
from dotpull.profile import Profile


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="clean")
def clean_group():
    """Remove stale links and orphaned artefacts."""


@clean_group.command(name="links")
@click.argument("profile_name")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--dry-run", is_flag=True, default=False, help="Preview without deleting.")
def cmd_links(profile_name: str, config: str, dry_run: bool) -> None:
    """Remove symlinks whose source file no longer exists."""
    cfg = _load(config)
    profiles: dict = cfg.get("profiles", {})
    if profile_name not in profiles:
        click.echo(f"error: unknown profile '{profile_name}'", err=True)
        raise SystemExit(1)

    profile = Profile(profile_name, profiles[profile_name], profiles)
    home_dir = Path(cfg.get("home_dir", Path.home()))
    dotfiles_dir = Path(cfg["dotfiles_dir"])

    result = clean_stale_links(profile, home_dir, dotfiles_dir, dry_run=dry_run)
    click.echo(result.summary())
    if result.removed:
        for p in result.removed:
            click.echo(f"  {'would remove' if dry_run else 'removed'}: {p}")


@clean_group.command(name="broken")
@click.argument("directory")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without deleting.")
def cmd_broken(directory: str, dry_run: bool) -> None:
    """Remove all broken symlinks under DIRECTORY."""
    target = Path(directory)
    if not target.exists():
        click.echo(f"error: directory '{directory}' does not exist", err=True)
        raise SystemExit(1)

    result = clean_broken_symlinks(target, dry_run=dry_run)
    click.echo(result.summary())
    if result.removed:
        for p in result.removed:
            click.echo(f"  {'would remove' if dry_run else 'removed'}: {p}")
