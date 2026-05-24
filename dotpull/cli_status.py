"""CLI commands for `dotpull status`."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.profile import Profile
from dotpull.status import check_profile_status


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="status")
def status_group():
    """Show sync status of profiles."""


@status_group.command("show")
@click.option("--config", default="dotpull.toml", show_default=True)
@click.option("--profile", "profile_name", default=None, help="Profile to inspect (default: all)")
@click.option("--home", default=None, help="Override home directory")
def cmd_show(config: str, profile_name: str | None, home: str | None):
    """Show sync status for one or all profiles."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    home_dir = Path(home) if home else Path.home()

    profiles_cfg = cfg.get("profiles", {})
    if not profiles_cfg:
        click.echo("No profiles defined.")
        raise SystemExit(0)

    names = [profile_name] if profile_name else list(profiles_cfg.keys())
    unknown = [n for n in names if n not in profiles_cfg]
    if unknown:
        click.echo(f"Unknown profile(s): {', '.join(unknown)}", err=True)
        raise SystemExit(1)

    all_healthy = True
    for name in names:
        profile = Profile(name=name, **profiles_cfg[name])
        st = check_profile_status(profile, dotfiles_dir, home_dir)
        icon = "✓" if st.healthy else "✗"
        click.echo(f"[{icon}] {st.summary()}")
        for r in st.details:
            if r.source_missing:
                click.echo(f"    MISSING source : {r.source}")
            elif r.target_missing:
                click.echo(f"    MISSING target : {r.target}")
            elif r.content_differs:
                click.echo(f"    DRIFTED        : {r.target}")
            elif not r.is_symlink:
                click.echo(f"    NOT SYMLINK    : {r.target}")
        if not st.healthy:
            all_healthy = False

    raise SystemExit(0 if all_healthy else 2)
