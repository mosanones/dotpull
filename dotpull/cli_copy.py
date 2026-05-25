"""cli_copy.py — CLI commands for copying files into the dotfiles repo."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.copy import CopyError, copy_into_repo


def _load(config_path: str) -> dict:
    cfg = load_config(Path(config_path))
    issues = validate_config(cfg)
    if issues:
        raise click.ClickException("\n".join(issues))
    return cfg


@click.group(name="copy")
def copy_group() -> None:
    """Copy files from the filesystem into the dotfiles repository."""


@copy_group.command("add")
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option("--dest", default=None, help="Relative path inside dotfiles dir.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing file.")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would happen.")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_add(
    source: str,
    dest: str | None,
    overwrite: bool,
    dry_run: bool,
    config: str,
) -> None:
    """Copy SOURCE into the dotfiles repository."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])

    try:
        result = copy_into_repo(
            source=Path(source),
            dotfiles_dir=dotfiles_dir,
            relative_dest=dest,
            overwrite=overwrite,
            dry_run=dry_run,
        )
    except CopyError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
    if not result.healthy:
        for err in result.errors:
            click.echo(f"  warning: {err}", err=True)
