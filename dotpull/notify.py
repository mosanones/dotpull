"""Notification system for dotpull events (sync, link, rollback, etc.)."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class NotifyLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class NotifyError(Exception):
    pass


@dataclass
class NotifyEvent:
    title: str
    message: str
    level: NotifyLevel = NotifyLevel.INFO
    profile: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "profile": self.profile,
            "tags": self.tags,
        }


def _notify_desktop(event: NotifyEvent) -> bool:
    """Attempt to send a desktop notification via notify-send. Returns True on success."""
    try:
        urgency = {"info": "low", "warning": "normal", "error": "critical"}.get(
            event.level.value, "normal"
        )
        subprocess.run(
            ["notify-send", "-u", urgency, event.title, event.message],
            check=True,
            capture_output=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _notify_echo(event: NotifyEvent) -> bool:
    """Fallback: print notification to stdout."""
    prefix = {"info": "[i]", "warning": "[!]", "error": "[x]"}.get(
        event.level.value, "[i]"
    )
    print(f"{prefix} {event.title}: {event.message}")
    return True


def send_notification(
    event: NotifyEvent,
    *,
    desktop: bool = True,
    fallback_echo: bool = True,
) -> bool:
    """Send a notification. Returns True if at least one backend succeeded."""
    sent = False
    if desktop:
        sent = _notify_desktop(event)
    if not sent and fallback_echo:
        sent = _notify_echo(event)
    return sent


def notify_sync(profile: str, *, success: bool) -> bool:
    level = NotifyLevel.INFO if success else NotifyLevel.ERROR
    msg = "completed successfully" if success else "failed"
    event = NotifyEvent(
        title="dotpull sync",
        message=f"Profile '{profile}' sync {msg}.",
        level=level,
        profile=profile,
        tags=["sync"],
    )
    return send_notification(event)


def notify_link(profile: str, *, success: bool) -> bool:
    level = NotifyLevel.INFO if success else NotifyLevel.ERROR
    msg = "applied" if success else "failed"
    event = NotifyEvent(
        title="dotpull link",
        message=f"Profile '{profile}' links {msg}.",
        level=level,
        profile=profile,
        tags=["link"],
    )
    return send_notification(event)
