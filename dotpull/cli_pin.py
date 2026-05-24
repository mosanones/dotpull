"""CLI commands for pin management."""

from __future__ import annotations

import click
from pathlib import Path

from dotpull.pin import pin_profile, unpin_profile, list_pins, PinError


def _load(ctx: click.Context) -> tuple:
    from dotpull.config import load_config, validate_config
    cfg = load_config()
    errs = validate_config(cfg)
    if errs:
        raise click.ClickException("Config errors: " + "; ".join(errs))
    dotfiles_dir = Path(cfg["dotfiles_dir"]).expanduser()
    return cfg, dotfiles_dir


@click.group("pin")
def pin_group() -> None:
    """Lock profiles to specific snapshot revisions."""


@pin_group.command("set")
@click.argument("profile")
@click.argument("snapshot")
@click.option("--note", default="", help="Optional note for this pin.")
def cmd_set(profile: str, snapshot: str, note: str) -> None:
    """Pin PROFILE to SNAPSHOT."""
    ctx = click.get_current_context()
    try:
        _, dotfiles_dir = _load(ctx)
        entry = pin_profile(dotfiles_dir, profile, snapshot, note=note)
        click.echo(f"Pinned '{entry.profile}' -> '{entry.snapshot}'")
        if note:
            click.echo(f"  Note: {note}")
    except PinError as exc:
        raise click.ClickException(str(exc))


@pin_group.command("remove")
@click.argument("profile")
def cmd_remove(profile: str) -> None:
    """Remove the pin for PROFILE."""
    ctx = click.get_current_context()
    _, dotfiles_dir = _load(ctx)
    removed = unpin_profile(dotfiles_dir, profile)
    if removed:
        click.echo(f"Unpinned '{profile}'.")
    else:
        click.echo(f"No pin found for '{profile}'.")


@pin_group.command("list")
def cmd_list() -> None:
    """List all active pins."""
    ctx = click.get_current_context()
    _, dotfiles_dir = _load(ctx)
    pins = list_pins(dotfiles_dir)
    if not pins:
        click.echo("No pins defined.")
        return
    for p in pins:
        note_str = f"  # {p.note}" if p.note else ""
        click.echo(f"  {p.profile:<20} -> {p.snapshot}  [{p.created_at}]{note_str}")
