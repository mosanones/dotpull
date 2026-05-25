"""CLI commands for viewing sync history."""

from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.history import load_history, filter_history


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="history")
def history_group():
    """View sync operation history."""


@history_group.command(name="show")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--profile", default=None, help="Filter by profile name.")
@click.option("--action", default=None, help="Filter by action type.")
@click.option("--limit", default=20, show_default=True, help="Max entries to show.")
def cmd_show(config: str, profile: str, action: str, limit: int):
    """Show recent history entries."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        entries = load_history(dotfiles_dir)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    entries = filter_history(entries, profile=profile, action=action, limit=limit)

    if not entries:
        click.echo("No history entries found.")
        return

    for e in reversed(entries):
        files_str = ", ".join(e.files_affected) if e.files_affected else "—"
        note_str = f"  # {e.note}" if e.note else ""
        click.echo(f"[{e.timestamp}] {e.action:10s} {e.profile}{note_str}")
        click.echo(f"  files: {files_str}")


@history_group.command(name="clear")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.confirmation_option(prompt="Clear all history?")
def cmd_clear(config: str):
    """Delete all history entries."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    history_path = dotfiles_dir / ".history.json"
    if history_path.exists():
        history_path.unlink()
        click.echo("History cleared.")
    else:
        click.echo("No history file found.")
