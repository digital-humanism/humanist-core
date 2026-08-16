"""Security-significant hardening tests for HACP builders.

These tests focus on protocol invariants and error paths rather than merely
increasing statement coverage.
"""
from __future__ import annotations

import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from humanist_core.hacp import (
    EnvelopeBuilder,
    TokenBuilder,
    SchemaValidationError,
    b64url_decode,
    verify,
)
from humanist_core.hacp.crypto import canonicalize_json, hash_sha256
from humanist_core.hacp.models import IntentEnvelope


@pytest.fixture()
def key():
    return Ed25519PrivateKey.generate()


def make_envelope(**overrides) -> IntentEnvelope:
    """Build a deterministic envelope suitable for token-builder tests."""
    builder = (
        EnvelopeBuilder()
        .hacp_version(overrides.get("hacp_version", "0.9"))
        .principal(overrides.get("principal", "agent_001"))
        .principal_kind(overrides.get("principal_kind", "system"))
        .intent_statement(overrides.get("intent_statement", "Read customer record"))
        .scope(
            verbs=overrides.get("verbs", ["read"]),
            resource_classes=overrides.get("resource_classes", ["customer_record"]),
            audiences=overrides.get("audiences", ["internal"]),
            reversibility=overrides.get("reversibility", ["reversible"]),
            externality=overrides.get("externality", ["internal"]),
            data_classes=overrides.get("data_classes", ["internal"]),
        )
        .issued_at(overrides.get("issued_at", 1_800_000_000))
        .expires_at(overrides.get("expires_at", 1_800_003_600))
        .signer_key_id(overrides.get("signer_key_id", "key-test-001"))
        .envelope_id(overrides.get("envelope_id", "env-test-001"))
    )

    if overrides.get("parent_envelope_id") is not None:
        builder.parent_envelope_id(overrides["parent_envelope_id"])

    if overrides.get("with_budget", True):
        builder.autonomy_budget(
            max_actions=overrides.get("max_actions", 10),
            expires_at=overrides.get("budget_expires_at", 1_800_003_600),
        )

    return builder.build_unsigned()


def test_envelope_requires_principal():
    """Fail closed when the authority principal is absent."""
    with pytest.raises(SchemaValidationError, match="principal is required"):
        EnvelopeBuilder().build_unsigned()


def test_scope_accepts_scalar_and_sequence_boundary_dimensions():
    """Wire scope dimensions normalize to arrays regardless of SDK input form."""
    env_scalar = (
        EnvelopeBuilder()
        .principal("agent")
        .scope(
            verbs=["read"],
            resource_classes=["record"],
            audiences=["internal"],
            reversibility="reversible",
            externality="internal",
            data_classes=["internal"],
        )
        .build_unsigned()
    )
    assert env_scalar.scope.reversibility == ["reversible"]
    assert env_scalar.scope.externality == ["internal"]

    env_sequence = (
        EnvelopeBuilder()
        .principal("agent")
        .scope(
            verbs=["read"],
            resource_classes=["record"],
            audiences=["internal"],
            reversibility=("reversible", "compensatable"),
            externality=("internal", "external"),
            data_classes=["internal"],
        )
        .build_unsigned()
    )
    assert env_sequence.scope.reversibility == ["reversible", "compensatable"]
    assert env_sequence.scope.externality == ["internal", "external"]


def test_envelope_explicit_protocol_fields_and_parent_are_preserved():
    env = make_envelope(
        hacp_version="0.9",
        principal_kind="delegated",
        intent_statement="Delegated read",
        parent_envelope_id="env-parent-001",
        with_budget=False,
    )
    wire = env.to_dict()

    assert wire["hacp_version"] == "0.9"
    assert wire["principal_kind"] == "delegated"
    assert wire["intent_statement"] == "Delegated read"
    assert wire["parent_envelope_id"] == "env-parent-001"
    assert "autonomy_budget" not in wire


def test_signed_envelope_b64url_contains_exact_signed_wire(key):
    signed = (
        EnvelopeBuilder()
        .principal("agent")
        .scope(
            verbs=["read"],
            resource_classes=["record"],
            audiences=["internal"],
            data_classes=["internal"],
        )
        .sign(key)
    )

    decoded = json.loads(b64url_decode(signed.to_b64url()))
    assert decoded == signed.to_dict()
    assert verify(
        canonicalize_json(signed.envelope.to_dict()),
        b64url_decode(signed.signature),
        key.public_key(),
    )


def test_http_action_requires_envelope():
    """An HTTP action must never be synthesized without its authority envelope."""
    with pytest.raises(
        SchemaValidationError,
        match=r"envelope must be set before http_action\(\)",
    ):
        TokenBuilder().http_action("GET", "/api/test")


@pytest.mark.parametrize(
    ("method", "expected_verb"),
    [
        ("GET", "read"),
        ("HEAD", "read"),
        ("POST", "create"),
        ("PUT", "update"),
        ("PATCH", "update"),
        ("DELETE", "delete"),
        ("OPTIONS", "options"),
    ],
)
def test_http_action_method_mapping(method, expected_verb):
    """HTTP methods map deterministically to HACP action verbs."""
    env = make_envelope()
    token = (
        TokenBuilder()
        .envelope(env)
        .http_action(method, "/api/test", body=b"payload")
        .build_unsigned()
    )

    # Recreate with an explicit ProposedAction via the builder's HTTP path and
    # inspect the builder-held action indirectly through its bound hash.
    reference = (
        TokenBuilder()
        .envelope(env)
        .http_action(
            method,
            "/api/test",
            body=b"payload",
            resource_class="customer_record",
            audience="internal",
            reversibility="reversible",
            externality="internal",
            data_class="internal",
        )
        .build_unsigned()
    )
    assert token.action_hash == reference.action_hash

    # The mapping itself is security-significant. Inspect the synthesized
    # object before token construction to ensure the expected verb is bound.
    builder = TokenBuilder().envelope(env).http_action(method, "/api/test")
    assert builder._proposed_action is not None
    assert builder._proposed_action.verb == expected_verb


def test_http_action_binds_scope_and_payload_hash():
    env = make_envelope()
    body = b'{"customer_id":123}'

    builder = TokenBuilder().envelope(env).http_action("POST", "/api/customer", body=body)
    action = builder._proposed_action

    assert action is not None
    assert action.hacp_version == "0.9"
    assert action.verb == "create"
    assert action.resource_class == "customer_record"
    assert action.resource_id == "/api/customer"
    assert action.audience == "internal"
    assert action.reversibility == "reversible"
    assert action.externality == "internal"
    assert action.data_class == "internal"
    assert action.payload_hash == hash_sha256(body)


def test_http_action_explicit_metadata_overrides_scope():
    env = make_envelope()

    builder = TokenBuilder().envelope(env).http_action(
        "PATCH",
        "/api/customer/123",
        body=b"{}",
        resource_class="profile",
        audience="partner",
        reversibility="compensatable",
        externality="external",
        data_class="personal",
    )
    action = builder._proposed_action

    assert action is not None
    assert action.verb == "update"
    assert action.resource_class == "profile"
    assert action.audience == "partner"
    assert action.reversibility == "compensatable"
    assert action.externality == "external"
    assert action.data_class == "personal"


@pytest.mark.parametrize(
    ("scope_overrides", "expected_field"),
    [
        ({"resource_classes": []}, "resource_classes"),
        ({"audiences": []}, "audiences"),
        ({"reversibility": []}, "reversibility"),
        ({"externality": []}, "externality"),
        ({"data_classes": []}, "data_classes"),
    ],
)
def test_http_action_fails_closed_on_missing_scope_dimension(
    scope_overrides, expected_field
):
    """Sidecar-compatible action synthesis must not invent missing scope values."""
    env = make_envelope(**scope_overrides)

    with pytest.raises(
        SchemaValidationError,
        match=rf"scope\.{expected_field} must contain at least one value",
    ):
        TokenBuilder().envelope(env).http_action("GET", "/api/test")


def test_token_requires_proposed_action():
    env = make_envelope()

    with pytest.raises(SchemaValidationError, match="proposed_action is required"):
        TokenBuilder().envelope(env).build_unsigned()


def test_token_rejects_missing_envelope_id():
    env = make_envelope()
    env.envelope_id = None

    with pytest.raises(
        SchemaValidationError,
        match="envelope.envelope_id is required",
    ):
        (
            TokenBuilder()
            .envelope(env)
            .proposed_action(
                verb="read",
                resource_class="customer_record",
                resource_id="/api/test",
                audience="internal",
                data_class="internal",
            )
            .build_unsigned()
        )


def test_invalid_decision_fails_closed():
    with pytest.raises(SchemaValidationError, match="Invalid decision"):
        TokenBuilder().decision("MAYBE")


@pytest.mark.parametrize("decision", ["ALLOW", "CHECKPOINT", "DENY"])
def test_valid_decisions_are_preserved(decision):
    env = make_envelope()
    token = (
        TokenBuilder()
        .envelope(env)
        .proposed_action(
            verb="read",
            resource_class="customer_record",
            resource_id="/api/test",
            audience="internal",
            data_class="internal",
        )
        .decision(decision)
        .build_unsigned()
    )
    assert token.decision == decision


def test_token_explicit_security_fields_are_bound_and_signed(key):
    env = make_envelope()

    signed = (
        TokenBuilder()
        .envelope(env)
        .http_action("GET", "/api/test")
        .constraints(
            method="GET",
            path="/api/test",
            max_uses=1,
            tool_name="customer_lookup",
            payload_hash=hash_sha256(b""),
        )
        .decision("ALLOW")
        .policy_digest("policy-sha256-test")
        .issued_at(1_800_000_100)
        .expires_at(1_800_000_200)
        .token_id("tok-test-001")
        .signer_key_id("key-token-001")
        .sign(key)
    )

    token = signed.token
    assert token.token_id == "tok-test-001"
    assert token.envelope_id == "env-test-001"
    assert token.principal == "agent_001"
    assert token.policy_digest == "policy-sha256-test"
    assert token.issued_at == 1_800_000_100
    assert token.expires_at == 1_800_000_200
    assert token.signer_key_id == "key-token-001"
    assert token.constraints is not None
    assert token.constraints.max_uses == 1
    assert token.constraints.tool_name == "customer_lookup"

    assert verify(
        canonicalize_json(token.to_dict()),
        b64url_decode(signed.signature),
        key.public_key(),
    )

    decoded = json.loads(b64url_decode(signed.to_b64url()))
    assert decoded == signed.to_dict()


def test_token_defaults_generate_identity_and_inherit_signer():
    env = make_envelope()

    token = (
        TokenBuilder()
        .envelope(env)
        .http_action("GET", "/api/test")
        .build_unsigned()
    )

    assert token.token_id
    assert token.issued_at > 0
    assert token.expires_at == env.expires_at
    assert token.signer_key_id == env.signer_key_id
    assert token.hacp_version == env.hacp_version


def test_token_canonicalize_is_deterministic_with_explicit_fields():
    env = make_envelope()

    def build():
        return (
            TokenBuilder()
            .envelope(env)
            .http_action("GET", "/api/test")
            .policy_digest("policy-1")
            .issued_at(1_800_000_010)
            .expires_at(1_800_000_020)
            .token_id("tok-1")
            .signer_key_id("key-1")
            .canonicalize()
        )

    assert build() == build()
