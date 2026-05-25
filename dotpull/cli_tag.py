"""CLI commands for managing profile tags."""

from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.tag import TagError, load_tag_store


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    issues = validate_config(cfg)
    if issues:
        raise click.ClickException("Config invalid: " + "; ".join(issues))
    dotfiles_dir = Path(cfg["dotfiles_dir"]).expanduser()
    return cfg, dotfiles_dir


@click.group(name="tag")
def tag_group():
    """Manage tags for profiles."""


@tag_group.command("add")
@click.argument("profile")
@click.argument("tag")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_add(profile: str, tag: str, config: str):
    """Add TAG to PROFILE."""
    _, dotfiles_dir = _load(config)
    store = load_tag_store(dotfiles_dir)
    store.add_tag(profile, tag)
    store.save()
    click.echo(f"Tagged '{profile}' with '{tag}'.")


@tag_group.command("remove")
@click.argument("profile")
@click.argument("tag")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_remove(profile: str, tag: str, config: str):
    """Remove TAG from PROFILE."""
    _, dotfiles_dir = _load(config)
    store = load_tag_store(dotfiles_dir)
    try:
        store.remove_tag(profile, tag)
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc
    store.save()
    click.echo(f"Removed tag '{tag}' from '{profile}'.")


@tag_group.command("list")
@click.option("--profile", default=None, help="Filter by profile name.")
@click.option("--tag", default=None, help="Filter by tag name.")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_list(profile: str | None, tag: str | None, config: str):
    """List tags or profiles matching a filter."""
    _, dotfiles_dir = _load(config)
    store = load_tag_store(dotfiles_dir)
    if profile:
        tags = store.tags_for(profile)
        if tags:
            click.echo("\n".join(tags))
        else:
            click.echo(f"No tags for profile '{profile}'.")
    elif tag:
        profiles = store.profiles_for(tag)
        if profiles:
            click.echo("\n".join(profiles))
        else:
            click.echo(f"No profiles with tag '{tag}'.")
    else:
        all_tags = store.all_tags()
        if all_tags:
            click.echo("\n".join(all_tags))
        else:
            click.echo("No tags defined.")
