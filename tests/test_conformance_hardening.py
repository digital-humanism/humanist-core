"""Coverage hardening for humanist_core.hacp.conformance.

These tests intentionally target defensive/fallback branches that are not
necessarily represented by the normative HACP vector set.  They do not alter
the normative 38/38 conformance result.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from humanist_core.hacp import conformance as conf
from humanist_core.hacp.crypto import b64url_encode, canonicalize_json, hash_sha256


@pytest.fixture()
def keypair():
    private_key = Ed25519PrivateKey.generate()
    return private_key, private_key.public_key()


def _sign_mapping(value: dict[str, Any], private_key: Ed25519PrivateKey) -> str:
    unsigned = {k: v for k, v in value.items() if k != "signature"}
    return b64url_encode(private_key.sign(canonicalize_json(unsigned)))


def _base_vector(private_key: Ed25519PrivateKey) -> dict[str, Any]:
    action = {
        "resource_class": "repo",
        "audience": "internal",
        "reversibility": "reversible",
        "externality": "internal",
        "data_class": "internal",
        "verb": "read",
        "destination": "local",
        "tool_name": "tool",
        "quantity": 1,
    }

    envelope = {
        "envelope_id": "env-1",
        "principal": "human-1",
        "principal_kind": "human",
        "issued_at": 100,
        "expires_at": 200,
        "signer_key_id": "key-ed25519-test-001",
        "scope": {
            "resource_classes": ["repo"],
            "audiences": ["internal"],
            "reversibility": ["reversible"],
            "externality": ["internal"],
            "data_classes": ["internal"],
            "verbs": ["read"],
            "destinations": ["local"],
            "tool_names": ["tool"],
            "max_quantity": 10,
        },
    }
    envelope["signature"] = _sign_mapping(envelope, private_key)

    return {
        "inputs": {
            "intent_envelope": envelope,
            "proposed_action": action,
        },
        "policy_context": {"current_time": 150},
    }


def _add_valid_token(
    vector: dict[str, Any],
    private_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    result = deepcopy(vector)
    inputs = result["inputs"]
    action = inputs["proposed_action"]
    envelope = inputs["intent_envelope"]

    token = {
        "token_id": "tok-1",
        "envelope_id": envelope["envelope_id"],
        "action_hash": hash_sha256(canonicalize_json(action)),
        "expires_at": 190,
        "signer_key_id": "key-ed25519-test-001",
    }
    token["signature"] = _sign_mapping(token, private_key)
    inputs["decision_token"] = token
    return result


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def test_as_list_tuple_and_scalar_branches():
    assert conf._as_list(("a", "b")) == ["a", "b"]
    assert conf._as_list("a") == ["a"]


@pytest.mark.parametrize("signature", [None, "", b"bytes", 123])
def test_verify_signature_rejects_non_string_or_empty(keypair, signature):
    _, public_key = keypair
    assert conf._verify_signature(public_key, b"payload", signature) is False


def test_verify_signature_rejects_bad_base64_or_bad_signature(keypair):
    _, public_key = keypair
    assert conf._verify_signature(public_key, b"payload", "***not-a-signature***") is False


def test_scope_without_mapping_is_exceeded():
    assert conf._scope_reason({}, {"scope": None}) == "SCOPE_EXCEEDED"


def test_scope_empty_mapping_allows_missing_optional_dimensions():
    assert conf._scope_reason({}, {"scope": {}}) is None


def test_scope_missing_required_action_attribute_is_unknown():
    assert (
        conf._scope_reason(
            {},
            {"scope": {"audiences": ["internal"]}},
        )
        == "UNKNOWN_ATTRIBUTE"
    )


def test_scope_boundary_crossing():
    assert (
        conf._scope_reason(
            {"audience": "external"},
            {"scope": {"audiences": ["internal"]}},
        )
        == "BOUNDARY_CROSSING"
    )


def test_scope_quantity_exceeded():
    assert (
        conf._scope_reason(
            {"quantity": 11},
            {"scope": {"max_quantity": 10}},
        )
        == "SCOPE_EXCEEDED"
    )


def test_scope_destination_missing_unknown():
    assert (
        conf._scope_reason(
            {},
            {"scope": {"destinations": ["local"]}},
        )
        == "UNKNOWN_ATTRIBUTE"
    )


def test_scope_destination_crossing():
    assert (
        conf._scope_reason(
            {"destination": "remote"},
            {"scope": {"destinations": ["local"]}},
        )
        == "BOUNDARY_CROSSING"
    )


def test_scope_destination_allowed_continues():
    assert (
        conf._scope_reason(
            {"destination": "local"},
            {"scope": {"destinations": ["local"]}},
        )
        is None
    )


def test_scope_tool_name_missing_unknown():
    assert (
        conf._scope_reason(
            {},
            {"scope": {"tool_names": ["tool"]}},
        )
        == "UNKNOWN_ATTRIBUTE"
    )


def test_scope_tool_name_crossing():
    assert (
        conf._scope_reason(
            {"tool_name": "other"},
            {"scope": {"tool_names": ["tool"]}},
        )
        == "BOUNDARY_CROSSING"
    )


def test_scope_tool_name_allowed():
    assert (
        conf._scope_reason(
            {"tool_name": "tool"},
            {"scope": {"tool_names": ["tool"]}},
        )
        is None
    )


# ---------------------------------------------------------------------------
# Provenance defensive branches
# ---------------------------------------------------------------------------

def test_verify_provenance_requires_payload(keypair):
    _, public_key = keypair
    assert conf._verify_provenance({}, None, public_key) is False


def test_verify_provenance_payload_canonicalization_failure(monkeypatch, keypair):
    _, public_key = keypair

    def boom(_value):
        raise ValueError("bad payload")

    monkeypatch.setattr(conf, "canonicalize_json", boom)

    event = {"payload": object()}
    assert conf._verify_provenance(event, None, public_key) is False


def test_verify_provenance_payload_hash_mismatch(keypair):
    _, public_key = keypair
    event = {
        "payload": {"x": 1},
        "payload_hash": "not-the-hash",
        "prev_event_hash": conf.GENESIS_HASH,
        "signature": "x",
    }
    assert conf._verify_provenance(event, None, public_key) is False


def test_verify_provenance_prior_canonicalization_failure(monkeypatch, keypair):
    _, public_key = keypair
    original = conf.canonicalize_json
    payload = {"x": 1}
    prior = {"bad_prior": object()}

    def selective(value):
        if isinstance(value, dict) and "bad_prior" in value:
            raise ValueError("bad prior")
        return original(value)

    monkeypatch.setattr(conf, "canonicalize_json", selective)

    event = {
        "payload": payload,
        "payload_hash": hash_sha256(original(payload)),
        "prev_event_hash": "anything",
        "signature": "anything",
    }
    assert conf._verify_provenance(event, prior, public_key) is False


def test_verify_provenance_wrong_previous_hash(keypair):
    _, public_key = keypair
    payload = {"x": 1}
    event = {
        "payload": payload,
        "payload_hash": hash_sha256(canonicalize_json(payload)),
        "prev_event_hash": "wrong",
        "signature": "anything",
    }
    assert conf._verify_provenance(event, None, public_key) is False


def test_verify_provenance_event_canonicalization_failure(monkeypatch, keypair):
    _, public_key = keypair
    original = conf.canonicalize_json
    calls = 0

    def second_call_fails(value):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("bad event")
        return original(value)

    monkeypatch.setattr(conf, "canonicalize_json", second_call_fails)

    payload = {"x": 1}
    event = {
        "payload": payload,
        "payload_hash": hash_sha256(original(payload)),
        "prev_event_hash": conf.GENESIS_HASH,
        "signature": "anything",
    }
    assert conf._verify_provenance(event, None, public_key) is False


# ---------------------------------------------------------------------------
# Evaluator input validation / context fallbacks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("vector", "message"),
    [
        ({}, "vector.inputs must be an object"),
        ({"inputs": {}}, "inputs.intent_envelope must be an object"),
        (
            {"inputs": {"intent_envelope": {}, "proposed_action": None}},
            "inputs.proposed_action must be an object",
        ),
        (
            {
                "inputs": {
                    "intent_envelope": {},
                    "proposed_action": {},
                    "decision_token": "bad",
                }
            },
            "inputs.decision_token must be an object when present",
        ),
    ],
)
def test_evaluator_rejects_malformed_top_level_inputs(keypair, vector, message):
    _, public_key = keypair
    with pytest.raises(ValueError, match=message.replace(".", r"\.")):
        conf.evaluate_conformance_vector(vector, public_key)


def test_context_falls_back_to_inputs_policy_context(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["policy_context"] = "not-a-mapping"
    vector["inputs"]["policy_context"] = {"current_time": 250}

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.decision == "DENY"
    assert result.reason_codes == ("ENVELOPE_EXPIRED",)


def test_context_defaults_to_empty_mapping(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector.pop("policy_context")
    vector["inputs"].pop("policy_context", None)

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.decision == "ALLOW"


# ---------------------------------------------------------------------------
# Runtime/checkpoint branches
# ---------------------------------------------------------------------------

def test_checkpoint_state_mapping_can_fall_through(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["checkpoint_state"] = {}

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.decision == "ALLOW"


def test_checkpoint_resolved_deny(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["checkpoint"] = {"state": "RESOLVED_DENY"}

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("CHECKPOINT_DENIED",)


def test_checkpoint_resolved_allow_by_human_continues(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["checkpoint"] = {
        "state": "RESOLVED_ALLOW",
        "resolver_principal_kind": "human",
    }

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.decision == "ALLOW"


def test_checkpoint_unknown_state_fails_closed(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["checkpoint"] = {"state": "ALIEN_STATE"}

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("INVALID_CHECKPOINT_STATE",)


# ---------------------------------------------------------------------------
# Token/key profile branches
# ---------------------------------------------------------------------------

def test_token_signer_key_revoked(keypair):
    private_key, public_key = keypair
    vector = _add_valid_token(_base_vector(private_key), private_key)
    vector["policy_context"]["revoked_keys"] = ["key-ed25519-test-001"]

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("KEY_REVOKED",)


def test_trusted_envelope_key_failure(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["policy_context"]["trusted_keys"] = ["another-key"]

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("SIGNATURE_FAILURE",)


def test_trusted_token_key_failure(keypair):
    private_key, public_key = keypair
    vector = _add_valid_token(_base_vector(private_key), private_key)
    vector["policy_context"]["trusted_keys"] = ["key-ed25519-test-001"]
    vector["inputs"]["decision_token"]["signer_key_id"] = "untrusted-token-key"

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("SIGNATURE_FAILURE",)


def test_hmac_envelope_signer_rejected(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["intent_envelope"]["signer_key_id"] = "legacy-hmac-key"

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("SIGNATURE_FAILURE",)


def test_hmac_token_signer_rejected(keypair):
    private_key, public_key = keypair
    vector = _add_valid_token(_base_vector(private_key), private_key)
    vector["inputs"]["decision_token"]["signer_key_id"] = "legacy-hmac-key"

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("SIGNATURE_FAILURE",)


def test_revoked_token(keypair):
    private_key, public_key = keypair
    vector = _add_valid_token(_base_vector(private_key), private_key)
    vector["policy_context"]["revoked_tokens"] = ["tok-1"]

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("TOKEN_REVOKED",)


# ---------------------------------------------------------------------------
# Provenance/evaluator + envelope lifecycle branches
# ---------------------------------------------------------------------------

def test_non_mapping_provenance_fails_closed(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["provenance_event"] = "not-an-object"

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("TRACEABILITY_FAILURE",)


def test_revoked_parent_envelope(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    envelope = vector["inputs"]["intent_envelope"]
    envelope["parent_envelope_id"] = "parent-1"
    envelope["signature"] = _sign_mapping(envelope, private_key)
    vector["policy_context"]["revoked_envelopes"] = ["parent-1"]

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("ENVELOPE_REVOKED",)


def test_envelope_signature_failure_sets_flag(keypair):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["intent_envelope"]["signature"] = "not-valid"

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("SIGNATURE_FAILURE",)
    assert result.envelope_signature_valid is False


def test_token_signature_failure_sets_flags(keypair):
    private_key, public_key = keypair
    vector = _add_valid_token(_base_vector(private_key), private_key)
    vector["inputs"]["decision_token"]["signature"] = "not-valid"

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.reason_codes == ("SIGNATURE_FAILURE",)
    assert result.envelope_signature_valid is True
    assert result.token_signature_valid is False


# ---------------------------------------------------------------------------
# Defensive type combinations in compound conditions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("checkpoint_state", "expected"),
    [
        ({"created_at": True, "timeout_seconds": 1}, "ALLOW"),
        ({"created_at": 100, "timeout_seconds": True}, "ALLOW"),
        ({"created_at": "100", "timeout_seconds": 1}, "ALLOW"),
        ({"created_at": 100, "timeout_seconds": "1"}, "ALLOW"),
    ],
)
def test_checkpoint_timeout_type_guards(keypair, checkpoint_state, expected):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["checkpoint_state"] = checkpoint_state

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.decision == expected


@pytest.mark.parametrize(
    "expires_at",
    [True, "120", None],
)
def test_checkpoint_expiry_type_guards_fall_to_open_checkpoint(
    keypair,
    expires_at,
):
    private_key, public_key = keypair
    vector = _base_vector(private_key)
    vector["inputs"]["checkpoint"] = {
        "state": "OPEN",
        "expires_at": expires_at,
    }

    result = conf.evaluate_conformance_vector(vector, public_key)
    assert result.decision == "CHECKPOINT"
    assert result.reason_codes == ("CHECKPOINT_REQUIRED",)


@pytest.mark.parametrize(
    ("quantity", "max_quantity"),
    [
        (True, 10),
        (1, True),
        ("11", 10),
        (11, "10"),
        (1, 10),
    ],
)
def test_scope_quantity_type_and_non_exceeding_guards(quantity, max_quantity):
    result = conf._scope_reason(
        {"quantity": quantity},
        {"scope": {"max_quantity": max_quantity}},
    )
    assert result is None
