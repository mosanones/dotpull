"""CLI commands for managing and running dotpull hooks."""
from __future__ import annotations

from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.hooks import HookError, collect_hooks, run_hooks
from dotpull.profile import resolve_profile


def _load(config_path: str):
    cfg = load_config(Path(config_path))
    validate_config(cfg)
    return cfg


@click.group(name="hooks")
def hooks_group():
    """Run pre/post sync hooks for a profile."""


@hooks_group.command("run")
@click.argument("stage", type=click.Choice(["pre_sync", "post_sync"]))
@click.option("--profile", "profile_name", default=None, help="Profile to use.")
@click.option("--config", "config_path", default="dotpull.yaml", show_default=True)
@click.option("--no-fail", is_flag=True, default=False, help="Continue on hook failure.")
@click.pass_context
def cmd_run(ctx, stage: str, profile_name: str, config_path: str, no_fail: bool):
    """Run hooks for STAGE (pre_sync or post_sync)."""
    cfg = _load(config_path)
    name = profile_name or cfg.get("default_profile", "default")
    try:
        profile = resolve_profile(cfg, name)
    except KeyError:
        raise click.ClickException(f"Unknown profile: {name}")

    commands = collect_hooks(profile, stage)
    if not commands:
        click.echo(f"No {stage} hooks defined for profile '{name}'.")
        return

    dotfiles_dir = Path(cfg["dotfiles_dir"])
    click.echo(f"Running {len(commands)} {stage} hook(s) for profile '{name}'...")
    try:
        results = run_hooks(commands, cwd=dotfiles_dir, stop_on_failure=not no_fail)
    except HookError as exc:
        raise click.ClickException(str(exc))

    for r in results:
        status = click.style("OK", fg="green") if r.success else click.style("FAIL", fg="red")
        click.echo(f"  [{status}] {r.hook}")
        if r.stdout:
            click.echo(f"         {r.stdout}")
        if r.stderr:
            click.echo(f"         stderr: {r.stderr}")


@hooks_group.command("list")
@click.option("--profile", "profile_name", default=None)
@click.option("--config", "config_path", default="dotpull.yaml", show_default=True)
def cmd_list(profile_name: str, config_path: str):
    """List configured hooks for a profile."""
    cfg = _load(config_path)
    name = profile_name or cfg.get("default_profile", "default")
    try:
        profile = resolve_profile(cfg, name)
    except KeyError:
        raise click.ClickException(f"Unknown profile: {name}")

    for stage in ("pre_sync", "post_sync"):
        cmds = collect_hooks(profile, stage)
        click.echo(f"{stage}:")
        if cmds:
            for cmd in cmds:
                click.echo(f"  - {cmd}")
        else:
            click.echo("  (none)")
