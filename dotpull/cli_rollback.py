"""CLI commands for rollback (restore from snapshot)."""

from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.snapshot import SnapshotError
from dotpull.rollback import rollback_profile, list_rollback_targets


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="rollback")
def rollback_group():
    """Restore dotfiles from a previous snapshot."""


@rollback_group.command("apply")
@click.argument("label")
@click.option("--profile", default="default", show_default=True, help="Profile name.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing files.")
@click.option("--config", default="dotpull.toml", show_default=True)
def cmd_apply(label: str, profile: str, dry_run: bool, config: str):
    """Restore dotfiles from snapshot LABEL."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        result = rollback_profile(dotfiles_dir, profile, label, dry_run=dry_run)
    except SnapshotError as exc:
        raise click.ClickException(str(exc))

    prefix = "[dry-run] " if dry_run else ""
    for rel in result.restored:
        click.echo(f"{prefix}restored: {rel}")
    for rel in result.skipped:
        click.echo(f"skipped (missing in snapshot): {rel}")
    for err in result.errors:
        click.echo(f"error: {err}", err=True)

    if result.success:
        click.echo(f"{prefix}Rollback to '{label}' complete. ({len(result.restored)} files)")
    else:
        raise click.ClickException("Rollback completed with errors.")


@rollback_group.command("list")
@click.option("--config", default="dotpull.toml", show_default=True)
def cmd_list(config: str):
    """List available rollback targets (snapshots)."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    targets = list_rollback_targets(dotfiles_dir)
    if not targets:
        click.echo("No snapshots available.")
        return
    for label in targets:
        click.echo(label)
