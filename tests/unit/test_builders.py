"""Unit tests for EnvelopeBuilder and TokenBuilder."""
import json
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from humanist_core.hacp import (
    EnvelopeBuilder,
    TokenBuilder,
    SchemaValidationError,
    b64url_decode,
    hash_action,
    verify,
)
from humanist_core.hacp.crypto import canonicalize_json


@pytest.fixture()
def key():
    return Ed25519PrivateKey.generate()


def base_builder():
    return (
        EnvelopeBuilder()
        .principal("agent_001")
        .scope(
            verbs=["read"],
            resource_classes=["record"],
            audiences=["internal"],
            data_classes=["public"],
        )
        .autonomy_budget(max_actions=10, expires_at=int(time.time()) + 3600)
    )


def test_envelope_defaults():
    env = base_builder().build_unsigned()
    assert env.principal == "agent_001"
    assert env.principal_kind == "system"
    assert env.envelope_id
    assert env.expires_at > env.issued_at


def test_invalid_principal_kind():
    with pytest.raises(SchemaValidationError):
        EnvelopeBuilder().principal_kind("robot")


def test_envelope_signature_verifies(key):
    signed = base_builder().sign(key)
    canonical = canonicalize_json(signed.envelope.to_dict())
    assert verify(canonical, b64url_decode(signed.signature), key.public_key())


def test_wire_contains_signature(key):
    signed = base_builder().sign(key)
    assert signed.to_dict()["signature"] == signed.signature


def test_b64url_wire_roundtrip(key):
    signed = base_builder().sign(key)
    decoded = json.loads(b64url_decode(signed.to_b64url()))
    assert decoded["principal"] == "agent_001"
    assert "signature" in decoded


def test_token_requires_envelope(key):
    with pytest.raises(SchemaValidationError):
        TokenBuilder().sign(key)


def test_token_action_hash_binding(key):
    env = base_builder().build_unsigned()
    signed_tok = (
        TokenBuilder()
        .envelope(env)
        .proposed_action(
            verb="read",
            resource_class="record",
            resource_id="/api/x/1",
            audience="internal",
            data_class="public",
        )
        .constraints(method="GET", path="/api/x/1", max_uses=1)
        .sign(key)
    )
    expected = hash_action(
        {
            "verb": "read",
            "resource_class": "record",
            "resource_id": "/api/x/1",
            "audience": "internal",
            "data_class": "public",
        }
    )
    assert signed_tok.token.action_hash == expected
    assert signed_tok.token.envelope_id == env.envelope_id