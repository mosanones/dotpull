"""CLI commands for managing sync schedules."""
from __future__ import annotations

import click
from pathlib import Path

from dotpull.schedule import ScheduleStore, ScheduleError, run_due
from dotpull.sync import sync_profile
from dotpull.config import load_config
from dotpull.profile import Profile


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    store_path = Path(cfg["dotfiles_dir"]) / ".dotpull" / "schedule.json"
    store = ScheduleStore.load(store_path)
    return cfg, store, store_path


def _format_entry(name: str, entry) -> str:
    """Format a single schedule entry for display.

    Returns a human-readable string such as:
        myprofile: every 3600s, last=1713000000, enabled
    """
    status = "enabled" if entry.enabled else "disabled"
    last = f"{entry.last_run:.0f}" if entry.last_run else "never"
    return f"{name}: every {entry.interval_seconds}s, last={last}, {status}"


@click.group(name="schedule")
def schedule_group():
    """Manage automatic sync schedules."""


@schedule_group.command("add")
@click.argument("profile")
@click.option("--interval", required=True, type=int, help="Interval in seconds")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_add(profile: str, interval: int, config: str):
    """Add or update a schedule for PROFILE."""
    cfg, store, store_path = _load(config)
    try:
        store.add(profile, interval)
        store.save(store_path)
        click.echo(f"Scheduled '{profile}' every {interval}s.")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@schedule_group.command("remove")
@click.argument("profile")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_remove(profile: str, config: str):
    """Remove the schedule for PROFILE."""
    cfg, store, store_path = _load(config)
    try:
        store.remove(profile)
        store.save(store_path)
        click.echo(f"Removed schedule for '{profile}'.")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@schedule_group.command("list")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_list(config: str):
    """List all scheduled profiles."""
    _, store, _ = _load(config)
    if not store.entries:
        click.echo("No schedules defined.")
        return
    for name, entry in store.entries.items():
        click.echo(_format_entry(name, entry))


@schedule_group.command("run-due")
@click.option("--config", default="dotpull.yaml", show_default=True)
def cmd_run_due(config: str):
    """Run sync for all due profiles and update timestamps."""
    cfg, store, store_path = _load(config)

    def do_sync(profile_name: str):
        profiles = cfg.get("profiles", {})
        p = Profile(name=profile_name, data=profiles.get(profile_name, {}))
        sync_profile(p, dotfiles_dir=Path(cfg["dotfiles_dir"]))

    ran = run_due(store, on_sync=do_sync)
    store.save(store_path)
    if ran:
        click.echo("Synced: " + ", ".join(ran))
    else:
        click.echo("Nothing due.")
