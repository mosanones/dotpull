"""Tests for dotpull.encrypt module."""

from __future__ import annotations

import pytest
from pathlib import Path

pytest.importorskip("cryptography", reason="cryptography package required")

from dotpull.encrypt import (
    EncryptError,
    EncryptResult,
    decrypt_file,
    encrypt_file,
    list_encrypted_files,
)

PASSPHRASE = "s3cr3t-pass"


@pytest.fixture
def tmp_files(tmp_path: Path):
    src = tmp_path / "secret.txt"
    src.write_text("my secret content")
    return tmp_path, src


def test_encrypt_file_creates_enc_file(tmp_files):
    tmp_path, src = tmp_files
    dest = tmp_path / "secret.txt.enc"
    result = encrypt_file(src, dest, PASSPHRASE)
    assert dest.exists()
    assert result.success
    assert dest.read_bytes() != src.read_bytes()


def test_decrypt_file_restores_content(tmp_files):
    tmp_path, src = tmp_files
    enc = tmp_path / "secret.txt.enc"
    encrypt_file(src, enc, PASSPHRASE)
    out = tmp_path / "secret_restored.txt"
    result = decrypt_file(enc, out, PASSPHRASE)
    assert result.success
    assert out.read_text() == "my secret content"


def test_decrypt_wrong_passphrase_raises(tmp_files):
    tmp_path, src = tmp_files
    enc = tmp_path / "secret.txt.enc"
    encrypt_file(src, enc, PASSPHRASE)
    with pytest.raises(EncryptError, match="Decryption failed"):
        decrypt_file(enc, tmp_path / "out.txt", "wrong-pass")


def test_encrypt_missing_source_raises(tmp_path: Path):
    with pytest.raises(EncryptError, match="Source file not found"):
        encrypt_file(tmp_path / "ghost.txt", tmp_path / "ghost.enc", PASSPHRASE)


def test_decrypt_missing_source_raises(tmp_path: Path):
    with pytest.raises(EncryptError, match="Encrypted file not found"):
        decrypt_file(tmp_path / "ghost.enc", tmp_path / "out.txt", PASSPHRASE)


def test_list_encrypted_files(tmp_path: Path):
    (tmp_path / "a.enc").write_bytes(b"x")
    (tmp_path / "b.enc").write_bytes(b"y")
    (tmp_path / "plain.txt").write_text("z")
    result = list_encrypted_files(tmp_path)
    names = [f.name for f in result]
    assert "a.enc" in names
    assert "b.enc" in names
    assert "plain.txt" not in names


def test_encrypt_creates_parent_dirs(tmp_path: Path):
    src = tmp_path / "src.txt"
    src.write_text("data")
    dest = tmp_path / "nested" / "dir" / "src.txt.enc"
    encrypt_file(src, dest, PASSPHRASE)
    assert dest.exists()
