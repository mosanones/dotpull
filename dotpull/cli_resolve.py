"""CLI commands for inspecting resolved variables."""

from __future__ import annotations

import click

from dotpull.config import load_config, validate_config
from dotpull.profile import Profile
from dotpull.resolve import resolve_variables, ResolveError


def _load(config_path: str):
    cfg = load_config(config_path)
    errs = validate_config(cfg)
    if errs:
        raise click.ClickException("Config errors: " + "; ".join(errs))
    return cfg


@click.group(name="resolve")
def resolve_group():
    """Inspect resolved variables for a profile."""


@resolve_group.command("show")
@click.option("--config", "config_path", default="dotpull.toml", show_default=True)
@click.option("--profile", "profile_name", default=None, help="Profile name (default: first profile)")
@click.option("--env/--no-env", default=False, help="Include DOTPULL_* environment variables")
@click.option("--prefix", default="DOTPULL_", show_default=True, help="Env var prefix to scan")
def cmd_show(config_path: str, profile_name: str | None, env: bool, prefix: str):
    """Print all resolved variables for a profile."""
    cfg = _load(config_path)
    profiles_cfg = cfg.get("profiles", {})
    if not profiles_cfg:
        raise click.ClickException("No profiles defined in config.")

    name = profile_name or next(iter(profiles_cfg))
    if name not in profiles_cfg:
        raise click.ClickException(f"Unknown profile: {name!r}")

    profile = Profile(name, profiles_cfg[name])
    try:
        resolved = resolve_variables(profile, cfg, include_env=env, env_prefix=prefix)
    except ResolveError as exc:
        raise click.ClickException(str(exc)) from exc

    if not resolved.variables:
        click.echo(f"No variables resolved for profile '{name}'.")
        return

    click.echo(f"Resolved variables for profile '{name}':")
    for key, val in sorted(resolved.variables.items()):
        source = resolved.sources.get(key, "?")
        click.echo(f"  {key} = {val!r}  [{source}]")


@resolve_group.command("get")
@click.argument("key")
@click.option("--config", "config_path", default="dotpull.toml", show_default=True)
@click.option("--profile", "profile_name", default=None)
@click.option("--env/--no-env", default=False)
def cmd_get(key: str, config_path: str, profile_name: str | None, env: bool):
    """Print the resolved value of a single variable."""
    cfg = _load(config_path)
    profiles_cfg = cfg.get("profiles", {})
    name = profile_name or (next(iter(profiles_cfg)) if profiles_cfg else None)
    if not name or name not in profiles_cfg:
        raise click.ClickException(f"Unknown profile: {name!r}")

    profile = Profile(name, profiles_cfg[name])
    resolved = resolve_variables(profile, cfg, include_env=env)
    val = resolved.get(key)
    if val is None:
        raise click.ClickException(f"Variable {key!r} not found.")
    click.echo(val)
