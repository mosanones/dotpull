"""Tests for dotpull.cli_encrypt CLI commands."""

from __future__ import annotations

import pytest
from pathlib import Path
from click.testing import CliRunner

pytest.importorskip("cryptography", reason="cryptography package required")

from dotpull.cli_encrypt import encrypt_group

PASSPHRASE = "test-passphrase"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def dotpull_env(tmp_path: Path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    config_file = tmp_path / "dotpull.yaml"
    config_file.write_text(f"dotfiles_dir: {dotfiles}\nprofiles:\n  default:\n    files: []\n")
    secret = dotfiles / "secret.txt"
    secret.write_text("top secret")
    return {"config": str(config_file), "dotfiles": dotfiles, "secret": secret}


def test_lock_creates_enc_file(runner, dotpull_env):
    result = runner.invoke(
        encrypt_group,
        ["lock", str(dotpull_env["secret"]), "--config", dotpull_env["config"],
         "--passphrase", PASSPHRASE],
    )
    assert result.exit_code == 0
    assert "Encrypted" in result.output
    enc = Path(str(dotpull_env["secret"]) + ".enc")
    assert enc.exists()


def test_unlock_restores_file(runner, dotpull_env):
    enc = Path(str(dotpull_env["secret"]) + ".enc")
    runner.invoke(
        encrypt_group,
        ["lock", str(dotpull_env["secret"]), "--config", dotpull_env["config"],
         "--passphrase", PASSPHRASE],
    )
    out = dotpull_env["dotfiles"] / "restored.txt"
    result = runner.invoke(
        encrypt_group,
        ["unlock", str(enc), "--config", dotpull_env["config"],
         "--passphrase", PASSPHRASE],
    )
    assert result.exit_code == 0
    assert "Decrypted" in result.output


def test_unlock_wrong_passphrase_exits(runner, dotpull_env):
    runner.invoke(
        encrypt_group,
        ["lock", str(dotpull_env["secret"]), "--config", dotpull_env["config"],
         "--passphrase", PASSPHRASE],
    )
    enc = Path(str(dotpull_env["secret"]) + ".enc")
    result = runner.invoke(
        encrypt_group,
        ["unlock", str(enc), "--config", dotpull_env["config"],
         "--passphrase", "wrong"],
    )
    assert result.exit_code != 0


def test_list_shows_enc_files(runner, dotpull_env):
    enc = dotpull_env["dotfiles"] / "data.enc"
    enc.write_bytes(b"fake")
    result = runner.invoke(
        encrypt_group,
        ["list", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "data.enc" in result.output


def test_list_empty_shows_message(runner, dotpull_env):
    result = runner.invoke(
        encrypt_group,
        ["list", "--config", dotpull_env["config"]],
    )
    assert result.exit_code == 0
    assert "No encrypted files found" in result.output
