"""Main CLI entry-point for dotpull."""

import click

from dotpull.cli_link import link_group
from dotpull.cli_template import template_group
from dotpull.cli_snapshot import snapshot_group
from dotpull.cli_watch import watch_group
from dotpull.cli_export import export_group


@click.group()
@click.version_option(prog_name="dotpull")
def cli():
    """dotpull — Sync and version your dotfiles across machines."""


cli.add_command(link_group)
cli.add_command(template_group)
cli.add_command(snapshot_group)
cli.add_command(watch_group)
cli.add_command(export_group)


if __name__ == "__main__":
    cli()
