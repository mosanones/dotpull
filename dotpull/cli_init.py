"""CLI commands for initialising a dotfiles directory."""

from __future__ import annotations

import click

from dotpull.init import init_dotfiles_dir


@click.group("init")
def init_group() -> None:
    """Initialise a new dotfiles directory."""


@init_group.command("create")
@click.argument("directory", default="~/dotfiles")
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Overwrite existing files.",
)
def cmd_create(directory: str, force: bool) -> None:
    """Scaffold DIRECTORY with default dotpull config and profile."""
    result = init_dotfiles_dir(directory, force=force)

    if result.created:
        click.echo(click.style("Created:", fg="green", bold=True))
        for path in result.created:
            click.echo(f"  + {path}")

    if result.skipped:
        click.echo(click.style("Skipped (already exists):", fg="yellow"))
        for path in result.skipped:
            click.echo(f"  ~ {path}")

    if result.errors:
        click.echo(click.style("Errors:", fg="red", bold=True))
        for err in result.errors:
            click.echo(f"  ! {err}")
        raise SystemExit(1)

    click.echo(
        click.style(
            f"\nDotfiles directory ready at {directory}",
            fg="green",
        )
    )
