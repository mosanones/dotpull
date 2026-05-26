"""CLI commands for dotpull stash."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.profile import resolve_profile
from dotpull.stash import StashError, load_index, pop_stash, stash_files


def _load(ctx: click.Context) -> tuple:
    cfg = load_config()
    issues = validate_config(cfg)
    if issues:
        raise click.ClickException("\n".join(issues))
    dotfiles_dir = Path(cfg["dotfiles_dir"]).expanduser()
    profiles_file = dotfiles_dir / "profiles.yaml"
    return cfg, dotfiles_dir, profiles_file


@click.group("stash")
def stash_group() -> None:
    """Temporarily stash and restore dotfile changes."""


@stash_group.command("save")
@click.argument("profile")
@click.argument("files", nargs=-1, required=True, type=click.Path())
@click.option("--message", "-m", default="", help="Optional stash message.")
def cmd_save(profile: str, files: tuple, message: str) -> None:
    """Save current state of FILES in PROFILE to the stash."""
    cfg, dotfiles_dir, profiles_file = _load(click.get_current_context())
    try:
        resolve_profile(profiles_file, profile)
    except KeyError:
        raise click.ClickException(f"Unknown profile: {profile}")
    file_paths = [Path(f).expanduser() for f in files]
    try:
        entry = stash_files(dotfiles_dir, profile, file_paths, message=message)
    except StashError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Stashed {len(entry.files)} file(s) → stash id: {entry.stash_id}")
    if message:
        click.echo(f"  Message: {message}")


@stash_group.command("pop")
@click.argument("stash_id")
@click.option("--dry-run", is_flag=True, help="Preview without restoring.")
def cmd_pop(stash_id: str, dry_run: bool) -> None:
    """Restore files from STASH_ID and remove the entry."""
    cfg, dotfiles_dir, _ = _load(click.get_current_context())
    try:
        entry = pop_stash(dotfiles_dir, stash_id, dry_run=dry_run)
    except StashError as exc:
        raise click.ClickException(str(exc))
    prefix = "[dry-run] Would restore" if dry_run else "Restored"
    click.echo(f"{prefix} {len(entry.files)} file(s) from stash {stash_id}.")
    for f in entry.files:
        click.echo(f"  {f}")


@stash_group.command("list")
def cmd_list() -> None:
    """List all stash entries."""
    cfg, dotfiles_dir, _ = _load(click.get_current_context())
    entries = load_index(dotfiles_dir)
    if not entries:
        click.echo("No stash entries found.")
        return
    for e in entries:
        msg = f"  [{e.message}]" if e.message else ""
        click.echo(f"{e.stash_id}  profile={e.profile}  files={len(e.files)}{msg}")
