"""Encryption support for sensitive dotfiles using symmetric key encryption."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore


class EncryptError(Exception):
    """Raised when encryption or decryption fails."""


@dataclass
class EncryptResult:
    path: Path
    success: bool
    message: str


def _derive_key(passphrase: str) -> bytes:
    """Derive a Fernet-compatible key from a passphrase."""
    digest = hashlib.sha256(passphrase.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_file(source: Path, dest: Path, passphrase: str) -> EncryptResult:
    """Encrypt *source* and write ciphertext to *dest*."""
    if Fernet is None:
        raise EncryptError("cryptography package is not installed")
    if not source.exists():
        raise EncryptError(f"Source file not found: {source}")
    key = _derive_key(passphrase)
    fernet = Fernet(key)
    plaintext = source.read_bytes()
    ciphertext = fernet.encrypt(plaintext)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(ciphertext)
    return EncryptResult(path=dest, success=True, message="encrypted")


def decrypt_file(source: Path, dest: Path, passphrase: str) -> EncryptResult:
    """Decrypt *source* and write plaintext to *dest*."""
    if Fernet is None:
        raise EncryptError("cryptography package is not installed")
    if not source.exists():
        raise EncryptError(f"Encrypted file not found: {source}")
    key = _derive_key(passphrase)
    fernet = Fernet(key)
    ciphertext = source.read_bytes()
    try:
        plaintext = fernet.decrypt(ciphertext)
    except InvalidToken as exc:
        raise EncryptError("Decryption failed: invalid passphrase or corrupt data") from exc
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(plaintext)
    return EncryptResult(path=dest, success=True, message="decrypted")


def list_encrypted_files(dotfiles_dir: Path) -> list[Path]:
    """Return all *.enc files under *dotfiles_dir*."""
    return sorted(dotfiles_dir.rglob("*.enc"))
