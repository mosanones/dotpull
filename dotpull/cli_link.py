"""CLI commands for managing dotfile symlinks (link / unlink / audit)."""

import sys
from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.link_manager import LinkManager
from dotpull.profile import resolve_profile


@click.group()
def link_group() -> None:
    """Manage dotfile symlinks."""


@link_group.command("link")
@click.argument("profile_name", default="default")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.option("--config", "config_path", default=None, help="Path to dotpull config file.")
def cmd_link(profile_name: str, force: bool, config_path: str | None) -> None:
    """Create symlinks for PROFILE_NAME (default: 'default')."""
    cfg = _load(config_path)
    manager, profile = _setup(cfg, profile_name)
    results = manager.apply(profile, force=force)
    _print_results(results, key="status")
    errors = [r for r in results if r["status"] == "error"]
    if errors:
        sys.exit(1)


@link_group.command("unlink")
@click.argument("profile_name", default="default")
@click.option("--config", "config_path", default=None, help="Path to dotpull config file.")
def cmd_unlink(profile_name: str, config_path: str | None) -> None:
    """Remove symlinks for PROFILE_NAME."""
    cfg = _load(config_path)
    manager, profile = _setup(cfg, profile_name)
    results = manager.remove(profile)
    for r in results:
        mark = "✓" if r["removed"] else "–"
        click.echo(f"  {mark}  {r['target']}")


@link_group.command("audit")
@click.argument("profile_name", default="default")
@click.option("--config", "config_path", default=None, help="Path to dotpull config file.")
def cmd_audit(profile_name: str, config_path: str | None) -> None:
    """Audit symlink health for PROFILE_NAME."""
    cfg = _load(config_path)
    manager, profile = _setup(cfg, profile_name)
    results = manager.audit(profile)
    _print_results(results, key="status")
    not_ok = [r for r in results if r["status"] != "ok"]
    if not_ok:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(config_path: str | None) -> dict:
    path = Path(config_path) if config_path else None
    cfg = load_config(path)
    validate_config(cfg)
    return cfg


def _setup(cfg: dict, profile_name: str):
    dotfiles_dir = Path(cfg["dotfiles_dir"]).expanduser()
    profile = resolve_profile(cfg, profile_name)
    manager = LinkManager(dotfiles_dir)
    return manager, profile


_STATUS_ICONS = {"ok": "✓", "linked": "✓", "missing": "?", "conflict": "!", "wrong": "✗", "error": "✗"}


def _print_results(results: list[dict], key: str) -> None:
    for r in results:
        status = r[key]
        icon = _STATUS_ICONS.get(status, " ")
        extra = f" — {r['error']}" if r.get("error") else ""
        click.echo(f"  {icon}  [{status:8s}]  {r['target']}{extra}")
