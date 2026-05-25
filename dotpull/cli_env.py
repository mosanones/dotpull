"""CLI commands for inspecting and injecting environment variables."""

from __future__ import annotations

import sys

import click

from dotpull.config import load_config, validate_config
from dotpull.env import EnvError, capture_env, required_env
from dotpull.profile import Profile


def _load(config_path: str):
    cfg = load_config(config_path)
    issues = validate_config(cfg)
    if issues:
        click.echo("Config errors:\n" + "\n".join(issues), err=True)
        sys.exit(1)
    return cfg


@click.group("env")
def env_group():
    """Inspect and inject environment variables for profiles."""


@env_group.command("show")
@click.option("--config", default="dotpull.yaml", show_default=True)
@click.option("--prefix", "prefixes", multiple=True, help="Filter by prefix (repeatable).")
def cmd_show(config: str, prefixes):
    """Print captured environment variables, optionally filtered by prefix."""
    _load(config)
    snapshot = capture_env(list(prefixes) if prefixes else None)
    if not snapshot.variables:
        click.echo("No matching environment variables found.")
        return
    for k, v in sorted(snapshot.variables.items()):
        click.echo(f"{k}={v}")


@env_group.command("check")
@click.argument("keys", nargs=-1, required=True)
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_check(keys, config: str):
    """Verify that required environment variables are set."""
    _load(config)
    try:
        found = required_env(list(keys))
    except EnvError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    for k, v in sorted(found.items()):
        click.echo(f"{k}={v}")
    click.echo(f"All {len(found)} variable(s) present.")
