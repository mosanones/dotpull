"""CLI commands for remote git sync operations."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.remote import RemoteError, remote_pull, remote_push, remote_status


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    errs = validate_config(cfg)
    if errs:
        raise click.ClickException("Config errors: " + "; ".join(errs))
    return cfg


@click.group("remote")
def remote_group():
    """Sync dotfiles with a remote git repository."""


@remote_group.command("push")
@click.option("--config", default="dotpull.toml", show_default=True)
@click.option("--message", "-m", default=None, help="Commit message")
def cmd_push(config: str, message: str | None):
    """Stage, commit, and push dotfiles to the remote."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        result = remote_push(dotfiles_dir, message=message)
    except RemoteError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.success:
        click.echo(f"✓ {result.message}")
        if result.output:
            click.echo(result.output)
    else:
        click.echo(f"✗ {result.message}", err=True)
        for e in result.errors:
            click.echo(f"  {e}", err=True)
        raise click.ClickException("Push failed")


@remote_group.command("pull")
@click.option("--config", default="dotpull.toml", show_default=True)
def cmd_pull(config: str):
    """Pull latest dotfiles from the remote."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        result = remote_pull(dotfiles_dir)
    except RemoteError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.success:
        click.echo(f"✓ {result.message}")
        if result.output:
            click.echo(result.output)
    else:
        click.echo(f"✗ {result.message}", err=True)
        for e in result.errors:
            click.echo(f"  {e}", err=True)
        raise click.ClickException("Pull failed")


@remote_group.command("status")
@click.option("--config", default="dotpull.toml", show_default=True)
def cmd_status(config: str):
    """Show git status of the dotfiles directory."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        result = remote_status(dotfiles_dir)
    except RemoteError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.output:
        click.echo(result.output)
    else:
        click.echo("Nothing to report — working tree clean.")
