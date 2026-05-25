"""Root CLI entry point for dotpull."""

from __future__ import annotations

import click

from dotpull.cli_link import link_group
from dotpull.cli_template import template_group
from dotpull.cli_snapshot import snapshot_group
from dotpull.cli_watch import watch_group
from dotpull.cli_export import export_group
from dotpull.cli_hooks import hooks_group
from dotpull.cli_encrypt import encrypt_group
from dotpull.cli_rollback import rollback_group
from dotpull.cli_pin import pin_group
from dotpull.cli_remote import remote_group
from dotpull.cli_schedule import schedule_group
from dotpull.cli_resolve import resolve_group
from dotpull.cli_status import status_group
from dotpull.cli_init import init_group
from dotpull.cli_migrate import migrate_group
from dotpull.cli_lint import lint_group
from dotpull.cli_tag import tag_group
from dotpull.cli_search import search_group
from dotpull.cli_compare import compare_group
from dotpull.cli_history import history_group


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
cli.add_command(rollback_group)
cli.add_command(pin_group)
cli.add_command(remote_group)
cli.add_command(schedule_group)
cli.add_command(resolve_group)
cli.add_command(status_group)
cli.add_command(init_group)
cli.add_command(migrate_group)
cli.add_command(lint_group)
cli.add_command(tag_group)
cli.add_command(search_group)
cli.add_command(compare_group)
cli.add_command(history_group)
