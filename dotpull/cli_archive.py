"""CLI commands for archive management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from dotpull.archive import ArchiveError, create_archive, list_archives, restore_archive
from dotpull.config import load_config, validate_config


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="archive")
def archive_group():
    """Compress and restore dotfile archives."""


@archive_group.command(name="create")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--label", default=None, help="Optional label for the archive.")
def cmd_create(config: str, label: Optional[str]):
    """Create a compressed archive of the dotfiles directory."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        result = create_archive(dotfiles_dir, label=label)
        click.echo(f"Archive created: {result.path}")
        click.echo(f"Files archived : {len(result.files)}")
        click.echo(f"SHA-256        : {result.checksum}")
    except ArchiveError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@archive_group.command(name="list")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_list(config: str):
    """List available archives."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    archives = list_archives(dotfiles_dir)
    if not archives:
        click.echo("No archives found.")
        return
    for a in archives:
        click.echo(f"{a.label}  {a.checksum[:12]}  {a.path}")


@archive_group.command(name="restore")
@click.argument("archive")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--target", default=None, help="Target directory (defaults to dotfiles_dir).")
@click.option("--overwrite", is_flag=True, default=False)
def cmd_restore(archive: str, config: str, target: Optional[str], overwrite: bool):
    """Restore files from an archive."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    archive_path = Path(archive)
    if not archive_path.is_absolute():
        archive_path = dotfiles_dir / ".archives" / archive
        if not archive_path.suffix:
            archive_path = archive_path.with_suffix(".tar.gz")
    dest = Path(target) if target else dotfiles_dir
    try:
        restored = restore_archive(archive_path, dest, overwrite=overwrite)
        click.echo(f"Restored {len(restored)} file(s) to {dest}")
    except ArchiveError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
