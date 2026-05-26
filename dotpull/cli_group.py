"""CLI commands for managing profile groups."""

from __future__ import annotations

import click

from dotpull.config import load_config, validate_config
from dotpull.group import GroupError, load_groups


def _load(config_path):
    cfg = load_config(config_path)
    validate_config(cfg)
    return cfg


@click.group(name="group")
def group_group():
    """Manage profile groups."""


@group_group.command(name="add")
@click.argument("group")
@click.argument("profile")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_add(group, profile, config):
    """Add PROFILE to GROUP."""
    cfg = _load(config)
    store = load_groups(cfg["dotfiles_dir"])
    try:
        store.add(group, profile)
        store.save()
        click.echo(f"Added '{profile}' to group '{group}'.")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_group.command(name="remove")
@click.argument("group")
@click.argument("profile")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_remove(group, profile, config):
    """Remove PROFILE from GROUP."""
    cfg = _load(config)
    store = load_groups(cfg["dotfiles_dir"])
    removed = store.remove(group, profile)
    store.save()
    if removed:
        click.echo(f"Removed '{profile}' from group '{group}'.")
    else:
        click.echo(f"'{profile}' was not in group '{group}'.")


@group_group.command(name="list")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--group", default=None, help="Filter to a specific group.")
def cmd_list(config, group):
    """List groups and their members."""
    cfg = _load(config)
    store = load_groups(cfg["dotfiles_dir"])
    groups = [group] if group else store.all_groups()
    if not groups:
        click.echo("No groups defined.")
        return
    for g in groups:
        members = store.members(g)
        click.echo(f"{g}: {', '.join(members) if members else '(empty)'}")


@group_group.command(name="delete")
@click.argument("group")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_delete(group, config):
    """Delete an entire GROUP."""
    cfg = _load(config)
    store = load_groups(cfg["dotfiles_dir"])
    deleted = store.delete_group(group)
    store.save()
    if deleted:
        click.echo(f"Deleted group '{group}'.")
    else:
        raise click.ClickException(f"Group '{group}' not found.")
