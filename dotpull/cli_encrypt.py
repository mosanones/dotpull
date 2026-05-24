"""CLI commands for encrypting and decrypting sensitive dotfiles."""

from __future__ import annotations

import os
from pathlib import Path

import click

from dotpull.config import load_config, validate_config
from dotpull.encrypt import EncryptError, decrypt_file, encrypt_file, list_encrypted_files


def _load(config_path: str | None):
    cfg = load_config(config_path)
    errs = validate_config(cfg)
    if errs:
        raise click.ClickException("Config errors: " + "; ".join(errs))
    return cfg


@click.group(name="encrypt")
def encrypt_group():
    """Encrypt and decrypt sensitive dotfiles."""


@encrypt_group.command("lock")
@click.argument("file", type=click.Path(exists=True))
@click.option("--config", default=None, help="Path to dotpull config file.")
@click.option("--passphrase", envvar="DOTPULL_PASSPHRASE", prompt=True, hide_input=True)
def cmd_lock(file: str, config: str | None, passphrase: str):
    """Encrypt FILE and save as FILE.enc."""
    _load(config)
    src = Path(file)
    dest = src.with_suffix(src.suffix + ".enc")
    try:
        result = encrypt_file(src, dest, passphrase)
        click.echo(f"Encrypted: {result.path}")
    except EncryptError as exc:
        raise click.ClickException(str(exc)) from exc


@encrypt_group.command("unlock")
@click.argument("file", type=click.Path(exists=True))
@click.option("--config", default=None, help="Path to dotpull config file.")
@click.option("--passphrase", envvar="DOTPULL_PASSPHRASE", prompt=True, hide_input=True)
def cmd_unlock(file: str, config: str | None, passphrase: str):
    """Decrypt FILE.enc and restore original FILE."""
    _load(config)
    src = Path(file)
    if not src.suffix == ".enc":
        raise click.ClickException("Expected a .enc file")
    dest = src.with_suffix("")  # strip .enc
    try:
        result = decrypt_file(src, dest, passphrase)
        click.echo(f"Decrypted: {result.path}")
    except EncryptError as exc:
        raise click.ClickException(str(exc)) from exc


@encrypt_group.command("list")
@click.option("--config", default=None, help="Path to dotpull config file.")
def cmd_list(config: str | None):
    """List all encrypted (.enc) files in the dotfiles directory."""
    cfg = _load(config)
    dotfiles_dir = Path(cfg["dotfiles_dir"])
    files = list_encrypted_files(dotfiles_dir)
    if not files:
        click.echo("No encrypted files found.")
        return
    for f in files:
        click.echo(str(f))
