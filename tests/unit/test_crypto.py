"""Unit tests for crypto primitives."""
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from humanist_core.hacp.crypto import (
    b64url_encode,
    b64url_decode,
    sign,
    verify,
    hash_sha256,
    export_private_key_pem,
    load_private_key_pem,
)


def test_b64url_no_padding():
    raw = b"\xfb\xff\xfe"
    encoded = b64url_encode(raw)
    assert "=" not in encoded
    assert b64url_decode(encoded) == raw


def test_b64url_roundtrip_str():
    assert b64url_decode(b64url_encode("hello")) == b"hello"


def test_sign_verify_roundtrip():
    key = Ed25519PrivateKey.generate()
    payload = b"payload"
    sig = sign(payload, key)
    assert len(sig) == 64
    assert verify(payload, sig, key.public_key())


def test_verify_rejects_tampered():
    key = Ed25519PrivateKey.generate()
    sig = sign(b"original", key)
    assert not verify(b"tampered", sig, key.public_key())


def test_sha256_known_vector():
    assert hash_sha256(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_pem_roundtrip():
    key = Ed25519PrivateKey.generate()
    pem = export_private_key_pem(key)
    loaded = load_private_key_pem(pem)
    payload = b"x"
    assert verify(payload, sign(payload, loaded), key.public_key())