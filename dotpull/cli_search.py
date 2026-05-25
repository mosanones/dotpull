"""CLI commands for searching profiles and dotfiles."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from dotpull.search import search_profiles, search_files_by_extension


def _load(config_path: str):
    from dotpull.config import load_config, validate_config
    from dotpull.profile import load_profiles

    cfg = load_config(Path(config_path))
    validate_config(cfg)
    profiles = load_profiles(Path(cfg["dotfiles_dir"]))
    return cfg, profiles


@click.group("search")
def search_group():
    """Search profiles, files, and variables."""


@search_group.command("query")
@click.argument("query")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--no-files", is_flag=True, help="Skip file path matching.")
@click.option("--no-vars", is_flag=True, help="Skip variable name matching.")
@click.option("--case-sensitive", is_flag=True)
def cmd_query(query, config, no_files, no_vars, case_sensitive):
    """Search profiles for files or variables matching QUERY."""
    _cfg, profiles = _load(config)
    results = search_profiles(
        profiles,
        query,
        search_files=not no_files,
        search_variables=not no_vars,
        case_sensitive=case_sensitive,
    )
    if not results:
        click.echo(f"No matches found for '{query}'.")
        sys.exit(0)
    for r in results:
        click.echo(f"[{r.profile_name}]")
        for f in r.matched_files:
            click.echo(f"  file: {f}")
        for v in r.matched_variables:
            click.echo(f"  var:  {v}")


@search_group.command("ext")
@click.argument("extension")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_ext(extension, config):
    """List profiles that manage files with EXTENSION (e.g. 'toml')."""
    _cfg, profiles = _load(config)
    results = search_files_by_extension(profiles, extension)
    if not results:
        click.echo(f"No profiles manage '.{extension.lstrip('.')}' files.")
        sys.exit(0)
    for r in results:
        click.echo(f"[{r.profile_name}]")
        for f in r.matched_files:
            click.echo(f"  {f}")
