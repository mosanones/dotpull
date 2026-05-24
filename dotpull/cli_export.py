"""CLI commands for exporting and importing dotfile profiles."""

import sys
from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.profile import Profile
from dotpull.export import export_profile, import_archive, ExportError


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    errs = validate_config(cfg)
    if errs:
        click.echo("Config errors: " + "; ".join(errs), err=True)
        sys.exit(1)
    return cfg


@click.group("export")
def export_group():
    """Export and import dotfile profiles."""


@export_group.command("create")
@click.option("--config", "config_path", default="dotpull.toml", show_default=True)
@click.option("--profile", "profile_name", default=None)
@click.option("--label", default=None, help="Human-readable label for the archive.")
@click.option("--output", "output_dir", default="exports", show_default=True)
def cmd_create(config_path, profile_name, label, output_dir):
    """Create a portable archive of a profile's dotfiles."""
    cfg = _load(config_path)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    profile_name = profile_name or cfg.get("default_profile", "default")

    try:
        profile = Profile.resolve(profile_name, cfg.get("profiles", {}))
    except KeyError:
        click.echo(f"Unknown profile: {profile_name}", err=True)
        sys.exit(1)

    try:
        archive = export_profile(profile, dotfiles_dir, Path(output_dir), label=label)
        click.echo(f"Exported to {archive}")
    except ExportError as exc:
        click.echo(f"Export failed: {exc}", err=True)
        sys.exit(1)


@export_group.command("import")
@click.argument("archive")
@click.option("--config", "config_path", default="dotpull.toml", show_default=True)
def cmd_import(archive, config_path):
    """Import dotfiles from a previously exported archive."""
    cfg = _load(config_path)
    dotfiles_dir = Path(cfg["dotfiles_dir"])

    try:
        restored = import_archive(Path(archive), dotfiles_dir)
        click.echo(f"Restored {len(restored)} file(s):")
        for f in restored:
            click.echo(f"  {f}")
    except ExportError as exc:
        click.echo(f"Import failed: {exc}", err=True)
        sys.exit(1)
