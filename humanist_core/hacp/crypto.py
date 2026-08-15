"""Cryptography primitives for HACP.

Pure Ed25519 (RFC 8032) + SHA-256 + Base64url (RFC 4648 §5, no padding).
Uses `cryptography` stdlib-compatible package. No external crypto dependencies.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Union

import jcs
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


def b64url_encode(data: Union[bytes, str]) -> str:
    """Base64url encode without padding."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(data: Union[str, bytes]) -> bytes:
    """Base64url decode with automatic padding restoration."""
    if isinstance(data, str):
        data = data.encode("ascii")
    # Restore padding: len % 4 == 0 -> 0, 1 -> invalid, 2 -> ==, 3 -> =
    padding = 4 - len(data) % 4
    if padding != 4:
        data += b"=" * padding
    return base64.urlsafe_b64decode(data)


def canonicalize_json(obj: dict) -> bytes:
    """JCS (RFC 8785) canonicalization with guaranteed bytes output."""
    data = jcs.canonicalize(obj)
    if isinstance(data, str):
        data = data.encode("utf-8")
    return data


def generate_keypair(seed: bytes | None = None) -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Generate an Ed25519 keypair.
    
    If `seed` is provided, deterministic key generation is NOT supported by
    the `cryptography` library directly. We raise NotImplementedError to
    maintain cryptographic safety. Use raw key loading for deterministic tests.
    """
    if seed is not None:
        raise NotImplementedError(
            "Deterministic Ed25519 key generation from seed is not exposed "
            "via cryptography.hazmat. Use load_private_key_raw() with a "
            "deterministic 32-byte secret for test fixtures."
        )
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def load_private_key_pem(pem_data: Union[str, bytes]) -> Ed25519PrivateKey:
    """Load an Ed25519 private key from PEM format (PKCS8)."""
    if isinstance(pem_data, str):
        pem_data = pem_data.encode("utf-8")
    key = serialization.load_pem_private_key(pem_data, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError(f"Expected Ed25519 private key, got {type(key).__name__}")
    return key


def export_private_key_pem(private_key: Ed25519PrivateKey) -> bytes:
    """Export Ed25519 private key to PEM format (PKCS8)."""
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def export_public_key_raw(public_key: Ed25519PublicKey) -> bytes:
    """Export raw 32-byte Ed25519 public key."""
    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def sign(payload: bytes, private_key: Ed25519PrivateKey) -> bytes:
    """Sign payload with Ed25519 private key. Returns 64-byte signature."""
    if not isinstance(payload, bytes):
        raise TypeError("Payload must be bytes (use canonicalize() first).")
    return private_key.sign(payload)


def verify(payload: bytes, signature: bytes, public_key: Ed25519PublicKey) -> bool:
    """Verify Ed25519 signature. Returns True if valid, raises on failure."""
    if not isinstance(payload, bytes):
        raise TypeError("Payload must be bytes.")
    if not isinstance(signature, bytes):
        raise TypeError("Signature must be bytes.")
    try:
        public_key.verify(signature, payload)
        return True
    except Exception:
        return False


def hash_sha256(data: Union[bytes, str]) -> str:
    """Return hex-encoded SHA-256 hash."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def hash_action(proposed_action_dict: dict) -> str:
    """Compute SHA-256 hash of canonical JSON representation of ProposedAction.
    
    This is used for `action_hash` in DecisionToken.
    """
    canonical = canonicalize_json(proposed_action_dict)
    return hash_sha256(canonical)


def generate_key_id() -> str:
    """Generate a random 16-byte key identifier (base64url encoded)."""
    return b64url_encode(secrets.token_bytes(16))