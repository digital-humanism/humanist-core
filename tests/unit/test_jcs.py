"""Unit tests for JSON Canonicalization (RFC 8785)."""
from humanist_core.hacp import EnvelopeBuilder
from humanist_core.hacp.crypto import canonicalize_json


def test_key_ordering():
    assert canonicalize_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_nested_ordering():
    assert (
        canonicalize_json({"b": 1, "a": {"d": 1, "c": 2}})
        == b'{"a":{"c":2,"d":1},"b":1}'
    )


def test_no_whitespace():
    canonical = canonicalize_json({"a": [1, 2], "b": "x"})
    assert b" " not in canonical


def test_envelope_canonicalization_deterministic():
    def build():
        return (
            EnvelopeBuilder()
            .principal("agent_001")
            .scope(
                verbs=["read"],
                resource_classes=[],
                audiences=["internal"],
                data_classes=["public"],
            )
            .autonomy_budget(max_actions=1, expires_at=1893456000)
            .issued_at(1000)
            .expires_at(2000)
            .signer_key_id("key-1")
            .envelope_id("env-1")
            .build_unsigned()
        )

    assert canonicalize_json(build().to_dict()) == canonicalize_json(build().to_dict())