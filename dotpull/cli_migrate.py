"""CLI commands for profile migration."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.migrate import MigrateError, copy_profile, rename_profile


def _load(config_path: str) -> dict:
    cfg = load_config(Path(config_path))
    errs = validate_config(cfg)
    if errs:
        raise click.ClickException("Config errors: " + "; ".join(errs))
    return cfg


@click.group(name="migrate")
def migrate_group() -> None:
    """Rename or copy profile definitions."""


@migrate_group.command("rename")
@click.argument("source")
@click.argument("destination")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite destination if it exists.")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_rename(source: str, destination: str, overwrite: bool, config: str) -> None:
    """Rename SOURCE profile to DESTINATION."""
    cfg = _load(config)
    profiles_path = Path(cfg.get("dotfiles_dir", "dotfiles")) / "profiles.yaml"
    try:
        result = rename_profile(profiles_path, source, destination, overwrite=overwrite)
        click.echo(result.message)
    except MigrateError as exc:
        raise click.ClickException(str(exc)) from exc


@migrate_group.command("copy")
@click.argument("source")
@click.argument("destination")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite destination if it exists.")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_copy(source: str, destination: str, overwrite: bool, config: str) -> None:
    """Copy SOURCE profile to DESTINATION (original kept)."""
    cfg = _load(config)
    profiles_path = Path(cfg.get("dotfiles_dir", "dotfiles")) / "profiles.yaml"
    try:
        result = copy_profile(profiles_path, source, destination, overwrite=overwrite)
        click.echo(result.message)
    except MigrateError as exc:
        raise click.ClickException(str(exc)) from exc
