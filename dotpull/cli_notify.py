"""CLI commands for dotpull notification management."""
from __future__ import annotations

import click

from dotpull.notify import (
    NotifyEvent,
    NotifyLevel,
    send_notification,
)


@click.group("notify")
def notify_group() -> None:
    """Manage and test dotpull notifications."""


@notify_group.command("send")
@click.argument("title")
@click.argument("message")
@click.option(
    "--level",
    type=click.Choice(["info", "warning", "error"]),
    default="info",
    show_default=True,
    help="Notification urgency level.",
)
@click.option("--profile", default=None, help="Associated profile name.")
@click.option("--desktop/--no-desktop", default=True, help="Use desktop notifications.")
def cmd_send(
    title: str,
    message: str,
    level: str,
    profile: str | None,
    desktop: bool,
) -> None:
    """Send a one-off notification."""
    event = NotifyEvent(
        title=title,
        message=message,
        level=NotifyLevel(level),
        profile=profile,
    )
    sent = send_notification(event, desktop=desktop, fallback_echo=True)
    if sent:
        click.echo("Notification sent.")
    else:
        click.echo("Failed to send notification.", err=True)
        raise SystemExit(1)


@notify_group.command("test")
@click.option("--desktop/--no-desktop", default=True)
def cmd_test(desktop: bool) -> None:
    """Send a test notification to verify the notification backend works."""
    event = NotifyEvent(
        title="dotpull test",
        message="Notification backend is working.",
        level=NotifyLevel.INFO,
        tags=["test"],
    )
    sent = send_notification(event, desktop=desktop, fallback_echo=True)
    if sent:
        click.echo("Test notification sent successfully.")
    else:
        click.echo("Test notification failed.", err=True)
        raise SystemExit(1)
