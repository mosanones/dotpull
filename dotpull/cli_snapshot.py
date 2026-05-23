"""CLI commands for snapshot management."""

import click
from pathlib import Path

from dotpull.snapshot import create_snapshot, list_snapshots, restore_snapshot, SnapshotError
from dotpull.config import load_config, validate_config


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="snapshot")
def snapshot_group():
    """Manage dotfile snapshots."""


@snapshot_group.command("create")
@click.option("--config", default="dotpull.toml", show_default=True)
@click.option("--label", default="", help="Optional label for the snapshot.")
def cmd_create(config, label):
    """Create a snapshot of the current dotfiles state."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        snap_path = create_snapshot(dotfiles_dir, label=label)
        click.echo(f"Snapshot created: {snap_path.name}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@snapshot_group.command("list")
@click.option("--config", default="dotpull.toml", show_default=True)
def cmd_list(config):
    """List all available snapshots."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    snapshots = list_snapshots(dotfiles_dir)
    if not snapshots:
        click.echo("No snapshots found.")
        return
    for snap in snapshots:
        label_part = f"  [{snap['label']}]" if snap.get("label") else ""
        file_count = len(snap.get("files", {}))
        click.echo(f"{snap['name']}{label_part}  ({file_count} files)")


@snapshot_group.command("restore")
@click.argument("name")
@click.option("--config", default="dotpull.toml", show_default=True)
def cmd_restore(name, config):
    """Restore dotfiles from a named snapshot."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        restored = restore_snapshot(dotfiles_dir, name)
        click.echo(f"Restored {len(restored)} file(s) from snapshot '{name}'.")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
