"""CLI commands for managing presets."""

from __future__ import annotations

import click
from pathlib import Path

from dotpull.config import load_config, validate_config
from dotpull.preset import add_preset, remove_preset, load_presets, PresetError


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="preset")
def preset_group():
    """Manage named variable presets."""


@preset_group.command(name="add")
@click.argument("name")
@click.option("--var", "-v", multiple=True, metavar="KEY=VALUE", help="Variable in KEY=VALUE format.")
@click.option("--description", "-d", default="", help="Optional description.")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_add(name, var, description, config):
    """Add or update a named preset."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    variables = {}
    for item in var:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {item}")
        k, v = item.split("=", 1)
        variables[k.strip()] = v.strip()
    try:
        preset = add_preset(dotfiles_dir, name, variables, description)
        click.echo(f"Preset '{preset.name}' saved with {len(preset.variables)} variable(s).")
    except PresetError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@preset_group.command(name="remove")
@click.argument("name")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_remove(name, config):
    """Remove a preset by name."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    try:
        remove_preset(dotfiles_dir, name)
        click.echo(f"Preset '{name}' removed.")
    except PresetError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@preset_group.command(name="list")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_list(config):
    """List all saved presets."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    presets = load_presets(dotfiles_dir)
    if not presets:
        click.echo("No presets defined.")
        return
    for name, preset in sorted(presets.items()):
        desc = f" — {preset.description}" if preset.description else ""
        click.echo(f"  {name}{desc}")
        for k, v in preset.variables.items():
            click.echo(f"    {k}={v}")
