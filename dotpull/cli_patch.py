"""CLI commands for managing dotfile patches."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from dotpull.config import load_config, validate_config
from dotpull.patch import apply_patches_for_profile, list_patches, PatchError
from dotpull.profile import Profile


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="patch")
def patch_group():
    """Apply and inspect patch-based overrides for dotfiles."""


@patch_group.command("apply")
@click.argument("profile")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--dry-run", is_flag=True, default=False, help="Simulate without writing.")
def cmd_apply(profile: str, config: str, dry_run: bool):
    """Apply patches for PROFILE to its managed files."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    profiles_data = cfg.get("profiles", {})

    if profile not in profiles_data:
        click.echo(f"Unknown profile: {profile}", err=True)
        raise SystemExit(1)

    p = Profile(profile, profiles_data[profile], profiles_data)
    target_files = [dotfiles_dir / f for f in p.files()]

    try:
        result = apply_patches_for_profile(
            profile, dotfiles_dir, target_files, dry_run=dry_run
        )
    except PatchError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    prefix = "[dry-run] " if dry_run else ""
    for f in result.patched:
        click.echo(f"{prefix}patched  {f}")
    for f in result.skipped:
        click.echo(f"{prefix}skipped  {f}")
    for e in result.errors:
        click.echo(f"error    {e}", err=True)

    if not result.healthy():
        raise SystemExit(1)
    click.echo(f"Done: {result.summary()}")


@patch_group.command("list")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--profile", default=None, help="Filter by profile name.")
def cmd_list(config: str, profile: Optional[str]):
    """List available patch files."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    patches = list_patches(dotfiles_dir, profile_name=profile)
    if not patches:
        click.echo("No patches found.")
        return
    for p in patches:
        click.echo(str(p))
