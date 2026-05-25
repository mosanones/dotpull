"""CLI commands for managing profile aliases."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.alias import AliasError, load, resolve_alias
from dotpull.config import load_config


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    dotfiles_dir = Path(cfg["dotfiles_dir"]).expanduser()
    return cfg, dotfiles_dir


@click.group("alias")
def alias_group():
    """Manage profile aliases."""


@alias_group.command("set")
@click.argument("name")
@click.argument("profile")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_set(name: str, profile: str, config: str):
    """Create or overwrite an alias NAME -> PROFILE."""
    _, dotfiles_dir = _load(config)
    try:
        store = load(dotfiles_dir)
        store.set(name, profile)
        store.save()
        click.echo(f"Alias '{name}' -> '{profile}' saved.")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_group.command("remove")
@click.argument("name")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_remove(name: str, config: str):
    """Remove an alias by NAME."""
    _, dotfiles_dir = _load(config)
    try:
        store = load(dotfiles_dir)
        removed = store.remove(name)
        if removed:
            store.save()
            click.echo(f"Alias '{name}' removed.")
        else:
            click.echo(f"Alias '{name}' not found.")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_group.command("list")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_list(config: str):
    """List all aliases."""
    _, dotfiles_dir = _load(config)
    try:
        store = load(dotfiles_dir)
        aliases = store.all()
        if not aliases:
            click.echo("No aliases defined.")
            return
        for name, profile in sorted(aliases.items()):
            click.echo(f"  {name:20s} -> {profile}")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_group.command("resolve")
@click.argument("name")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_resolve(name: str, config: str):
    """Print the profile that NAME resolves to."""
    _, dotfiles_dir = _load(config)
    try:
        store = load(dotfiles_dir)
        click.echo(resolve_alias(store, name))
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
