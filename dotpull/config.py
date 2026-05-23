"""Configuration loader and validator for dotpull profiles."""

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "dotpull" / "config.yaml"
DEFAULT_DOTFILES_DIR = Path.home() / ".dotfiles"


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load and return the dotpull configuration from a YAML file."""
    path = config_path or Path(os.environ.get("DOTPULL_CONFIG", DEFAULT_CONFIG_PATH))

    if not path.exists():
        return _default_config()

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    return _merge_with_defaults(data)


def _default_config() -> dict[str, Any]:
    """Return a sensible default configuration."""
    return {
        "dotfiles_dir": str(DEFAULT_DOTFILES_DIR),
        "active_profile": "default",
        "profiles": {},
        "symlink": True,
        "backup": True,
        "backup_dir": str(Path.home() / ".dotfiles_backup"),
    }


def _merge_with_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Merge user config with defaults, ensuring required keys exist."""
    defaults = _default_config()
    defaults.update(data)
    return defaults


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate configuration and return a list of error messages."""
    errors = []

    dotfiles_dir = Path(config.get("dotfiles_dir", ""))
    if not dotfiles_dir.exists():
        errors.append(f"dotfiles_dir does not exist: {dotfiles_dir}")

    if not config.get("active_profile"):
        errors.append("active_profile must be set")

    profiles = config.get("profiles", {})
    if not isinstance(profiles, dict):
        errors.append("profiles must be a mapping")

    return errors
