"""Preset management: save and load named variable sets for quick profile bootstrapping."""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class PresetError(Exception):
    pass


@dataclass
class Preset:
    name: str
    variables: Dict[str, str] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "variables": self.variables,
        }

    @staticmethod
    def from_dict(data: dict) -> "Preset":
        return Preset(
            name=data["name"],
            description=data.get("description", ""),
            variables=data.get("variables", {}),
        )


def _preset_path(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / ".dotpull" / "presets.yaml"


def load_presets(dotfiles_dir: Path) -> Dict[str, Preset]:
    path = _preset_path(dotfiles_dir)
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise PresetError(f"Invalid presets file: {path}")
    return {k: Preset.from_dict(v) for k, v in raw.items()}


def save_presets(dotfiles_dir: Path, presets: Dict[str, Preset]) -> None:
    path = _preset_path(dotfiles_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump({k: v.to_dict() for k, v in presets.items()}, default_flow_style=False))


def add_preset(dotfiles_dir: Path, name: str, variables: Dict[str, str], description: str = "") -> Preset:
    if not name:
        raise PresetError("Preset name must not be empty.")
    presets = load_presets(dotfiles_dir)
    preset = Preset(name=name, variables=variables, description=description)
    presets[name] = preset
    save_presets(dotfiles_dir, presets)
    return preset


def remove_preset(dotfiles_dir: Path, name: str) -> None:
    presets = load_presets(dotfiles_dir)
    if name not in presets:
        raise PresetError(f"Preset '{name}' not found.")
    del presets[name]
    save_presets(dotfiles_dir, presets)


def apply_preset(dotfiles_dir: Path, name: str, profile_vars: Dict[str, str]) -> Dict[str, str]:
    """Merge preset variables into profile_vars (profile vars take precedence)."""
    presets = load_presets(dotfiles_dir)
    if name not in presets:
        raise PresetError(f"Preset '{name}' not found.")
    merged = dict(presets[name].variables)
    merged.update(profile_vars)
    return merged
