"""Security-significant hardening tests for HACP crypto primitives."""
from __future__ import annotations

import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import humanist_core.hacp.crypto as crypto
from humanist_core.hacp.crypto import (
    b64url_decode,
    b64url_encode,
    canonicalize_json,
    export_private_key_pem,
    export_public_key_raw,
    generate_key_id,
    generate_keypair,
    hash_action,
    hash_sha256,
    load_private_key_pem,
    sign,
    verify,
)


def test_generate_keypair_returns_matching_ed25519_pair():
    private_key, public_key = generate_keypair()
    payload = b"hacp-security-test"
    signature = sign(payload, private_key)

    assert verify(payload, signature, public_key)


def test_generate_keypair_rejects_seeded_generation():
    """The public helper must not pretend to support an unsafe seed API."""
    with pytest.raises(NotImplementedError, match="Deterministic Ed25519"):
        generate_keypair(seed=b"x" * 32)


def test_load_private_key_pem_accepts_string_input():
    key = Ed25519PrivateKey.generate()
    pem_text = export_private_key_pem(key).decode("ascii")

    loaded = load_private_key_pem(pem_text)

    payload = b"payload"
    assert verify(payload, sign(payload, loaded), key.public_key())


def test_load_private_key_pem_rejects_non_ed25519_key():
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = rsa_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with pytest.raises(TypeError, match="Expected Ed25519 private key"):
        load_private_key_pem(pem)


def test_export_public_key_raw_is_exactly_32_bytes():
    key = Ed25519PrivateKey.generate()

    raw = export_public_key_raw(key.public_key())

    assert isinstance(raw, bytes)
    assert len(raw) == 32


def test_sign_rejects_non_bytes_payload():
    key = Ed25519PrivateKey.generate()

    with pytest.raises(TypeError, match="Payload must be bytes"):
        sign("not-bytes", key)  # type: ignore[arg-type]


def test_verify_rejects_non_bytes_payload():
    key = Ed25519PrivateKey.generate()
    signature = sign(b"payload", key)

    with pytest.raises(TypeError, match="Payload must be bytes"):
        verify("payload", signature, key.public_key())  # type: ignore[arg-type]


def test_verify_rejects_non_bytes_signature():
    key = Ed25519PrivateKey.generate()

    with pytest.raises(TypeError, match="Signature must be bytes"):
        verify(b"payload", "signature", key.public_key())  # type: ignore[arg-type]


def test_b64url_decode_accepts_bytes_and_no_padding_branch():
    raw = b"abc"  # base64url is YWJj: length is already divisible by 4
    encoded = b64url_encode(raw).encode("ascii")

    assert encoded == b"YWJj"
    assert b64url_decode(encoded) == raw


def test_b64url_roundtrip_binary_edge_values():
    raw = bytes(range(256))

    encoded = b64url_encode(raw)

    assert "=" not in encoded
    assert b64url_decode(encoded) == raw


def test_canonicalize_json_converts_string_result_to_bytes(monkeypatch):
    """Cover the SDK compatibility branch if a JCS implementation returns str."""
    monkeypatch.setattr(
        crypto.jcs,
        "canonicalize",
        lambda obj: '{"a":1}',
    )

    assert canonicalize_json({"a": 1}) == b'{"a":1}'


def test_hash_sha256_accepts_string_input():
    assert hash_sha256("abc") == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


def test_hash_action_is_canonical_order_independent():
    action_a = {
        "verb": "read",
        "resource_class": "record",
        "resource_id": "/api/1",
        "audience": "internal",
        "data_class": "internal",
    }
    action_b = {
        "data_class": "internal",
        "audience": "internal",
        "resource_id": "/api/1",
        "resource_class": "record",
        "verb": "read",
    }

    assert hash_action(action_a) == hash_action(action_b)


def test_hash_action_changes_when_security_semantics_change():
    base = {
        "verb": "read",
        "resource_class": "record",
        "resource_id": "/api/1",
        "audience": "internal",
        "data_class": "internal",
    }
    changed = dict(base)
    changed["audience"] = "external"

    assert hash_action(base) != hash_action(changed)


def test_generate_key_id_has_128_bits_of_decoded_random_material():
    key_id = generate_key_id()

    raw = b64url_decode(key_id)

    assert len(raw) == 16
    assert "=" not in key_id


def test_canonicalized_payload_is_valid_utf8_json():
    payload = {
        "z": "Привет",
        "a": [1, True, None],
    }

    canonical = canonicalize_json(payload)

    assert isinstance(canonical, bytes)
    assert json.loads(canonical.decode("utf-8")) == payload
