"""CLI commands for the watch feature."""

import click
from pathlib import Path

from dotpull.config import load_config, validate_config
from dotpull.profile import resolve_profile
from dotpull.link_manager import LinkManager
from dotpull.watch import watch_profile, WatchError


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="watch")
def watch_group():
    """Watch dotfiles for changes and re-link automatically."""


@watch_group.command("start")
@click.option("--config", default="dotpull.toml", show_default=True, help="Config file path.")
@click.option("--profile", "profile_name", default=None, help="Profile to watch (default from config).")
@click.option("--interval", default=2.0, show_default=True, help="Poll interval in seconds.")
def cmd_start(config: str, profile_name: str, interval: float):
    """Start watching and re-link on file changes."""
    cfg = _load(config)
    name = profile_name or cfg.get("default_profile", "default")

    try:
        profile = resolve_profile(name, cfg)
    except KeyError:
        raise click.ClickException(f"Unknown profile: {name}")

    dotfiles_dir = Path(cfg["dotfiles_dir"])
    home_dir = Path(cfg.get("home_dir", "~")).expanduser()
    manager = LinkManager(dotfiles_dir, home_dir)

    def on_change(changed: list[str]):
        click.echo(f"[watch] Changed: {', '.join(changed)} — re-linking...")
        results = manager.apply(profile)
        errors = [r for r in results if not r.get("ok")]
        if errors:
            for e in errors:
                click.echo(f"  [error] {e}", err=True)
        else:
            click.echo(f"  [watch] Re-link complete ({len(results)} link(s)).")

    click.echo(f"Watching profile '{name}' every {interval}s. Press Ctrl+C to stop.")
    try:
        watch_profile(dotfiles_dir, profile.files, on_change, interval=interval)
    except WatchError as exc:
        raise click.ClickException(str(exc))
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")
