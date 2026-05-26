"""CLI commands for scaffolding new profiles."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from dotpull.config import load_config, validate_config
from dotpull.scaffold import ScaffoldError, scaffold_profile


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    issues = validate_config(cfg)
    if issues:
        raise click.ClickException("Config invalid: " + "; ".join(issues))
    return cfg


@click.group(name="scaffold")
def scaffold_group():
    """Scaffold new profiles and dotfile stubs."""


@scaffold_group.command(name="create")
@click.argument("profile_name")
@click.option("--file", "files", multiple=True, metavar="REL_PATH",
              help="Sample dotfile path(s) to stub inside the repo.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview changes without writing anything.")
@click.option("--config", "config_path", default="dotpull.yaml",
              show_default=True, help="Path to dotpull config file.")
def cmd_create(
    profile_name: str,
    files: tuple,
    dry_run: bool,
    config_path: str,
):
    """Scaffold a new PROFILE_NAME with optional file stubs."""
    cfg = _load(config_path)
    dotfiles_dir = Path(cfg["dotfiles_dir"])

    try:
        result = scaffold_profile(
            dotfiles_dir=dotfiles_dir,
            profile_name=profile_name,
            sample_files=list(files) if files else None,
            dry_run=dry_run,
        )
    except ScaffoldError as exc:
        raise click.ClickException(str(exc))

    click.echo(result.summary())
    if not result.healthy():
        click.echo("Nothing to scaffold.")
