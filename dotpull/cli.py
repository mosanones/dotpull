"""Main CLI entry point for dotpull."""

from __future__ import annotations

import click

from dotpull.cli_link import link_group
from dotpull.cli_template import template_group
from dotpull.cli_snapshot import snapshot_group
from dotpull.cli_watch import watch_group
from dotpull.cli_export import export_group
from dotpull.cli_hooks import hooks_group
from dotpull.cli_encrypt import encrypt_group


@click.group()
@click.version_option()
def cli():
    """dotpull — Sync and version your dotfiles across machines."""


cli.add_command(link_group)
cli.add_command(template_group)
cli.add_command(snapshot_group)
cli.add_command(watch_group)
cli.add_command(export_group)
cli.add_command(hooks_group)
cli.add_command(encrypt_group)
