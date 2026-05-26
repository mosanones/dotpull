"""CLI commands for the promote feature."""
from __future__ import annotations

import sys
from pathlib import Path

import click
import yaml

from dotpull.promote import promote_profile, PromoteError
from dotpull.profile import Profile


def _load(config_path: str):
    from dotpull.config import load_config, validate_config
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


def _resolve_profile(name: str, cfg: dict) -> Profile:
    profiles_path = Path(cfg["dotfiles_dir"]) / "profiles.yaml"
    if not profiles_path.exists():
        raise PromoteError(f"profiles.yaml not found at {profiles_path}")
    raw = yaml.safe_load(profiles_path.read_text()) or {}
    if name not in raw:
        raise PromoteError(f"Profile '{name}' not found")
    data = raw[name]
    return Profile(
        name=name,
        files=data.get("files", {}),
        variables=data.get("variables", {}),
        extends=data.get("extends"),
    )


def _save_profile(profile: Profile, cfg: dict) -> None:
    profiles_path = Path(cfg["dotfiles_dir"]) / "profiles.yaml"
    raw = yaml.safe_load(profiles_path.read_text()) or {} if profiles_path.exists() else {}
    raw[profile.name] = {
        "files": dict(profile.files),
        "variables": dict(profile.variables),
    }
    if profile.extends:
        raw[profile.name]["extends"] = profile.extends
    profiles_path.write_text(yaml.dump(raw, default_flow_style=False))


@click.group(name="promote")
def promote_group():
    """Promote variables and files from one profile into another."""


@promote_group.command(name="apply")
@click.argument("source")
@click.argument("target")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in target.")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_apply(source: str, target: str, overwrite: bool, config: str):
    """Promote SOURCE profile's content into TARGET profile."""
    try:
        cfg = _load(config)
        src = _resolve_profile(source, cfg)
        tgt = _resolve_profile(target, cfg)
        result = promote_profile(src, tgt, overwrite=overwrite)
        _save_profile(tgt, cfg)
        click.echo(result.summary())
    except PromoteError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
