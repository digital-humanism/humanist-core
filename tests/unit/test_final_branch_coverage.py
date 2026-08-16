"""Final branch-coverage tests for humanist-core.

Targets only the remaining partial/missed branches reported after the
HACP conformance hardening suite.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from humanist_core.boundary import SemanticAction, SemanticDeltaGuard
from humanist_core.hacp import conformance as conf
from humanist_core.hacp.crypto import b64url_encode, canonicalize_json, hash_sha256
from humanist_core.integrations import langchain_guard
from humanist_core.integrations.langchain_guard import AgencyGuardCallback
from humanist_core.safe_harbor import SafeHarborLedger


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
        "envelope_id": "env-final-coverage",
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


def _add_token(
    vector: dict[str, Any],
    private_key: Ed25519PrivateKey,
    *,
    signer_key_id: str = "key-ed25519-test-001",
) -> dict[str, Any]:
    result = deepcopy(vector)
    inputs = result["inputs"]
    action = inputs["proposed_action"]
    envelope = inputs["intent_envelope"]

    token = {
        "token_id": "tok-final-coverage",
        "envelope_id": envelope["envelope_id"],
        "action_hash": hash_sha256(canonicalize_json(action)),
        "expires_at": 190,
        "signer_key_id": signer_key_id,
    }
    token["signature"] = _sign_mapping(token, private_key)
    inputs["decision_token"] = token
    return result


# ---------------------------------------------------------------------------
# boundary.py: same-category changes must NOT become semantic boundaries.
# Covers 64->68 and 71->75.
# ---------------------------------------------------------------------------

def test_semantic_delta_same_verb_category_does_not_add_change():
    guard = SemanticDeltaGuard()

    original = SemanticAction(
        verb="read",
        object="doc",
        audience="requester",
    )
    proposed = SemanticAction(
        verb="analyse",  # different verb, same read_write category
        object="doc",
        audience="requester",
    )

    delta = guard.compare(original, proposed)

    assert "verb" not in delta.dimensions_changed
    assert delta.boundary_type == "other"


def test_semantic_delta_same_audience_category_does_not_add_change():
    guard = SemanticDeltaGuard()

    original = SemanticAction(
        verb="read",
        object="doc",
        audience="requester",
    )
    proposed = SemanticAction(
        verb="read",
        object="doc",
        audience="self",  # different audience, same internal_external category
    )

    delta = guard.compare(original, proposed)

    assert "audience" not in delta.dimensions_changed
    assert delta.boundary_type == "other"


# ---------------------------------------------------------------------------
# conformance.py remaining paths.
# ---------------------------------------------------------------------------

def test_checkpoint_resolved_allow_human_continues_to_gate_2():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    vector = _base_vector(private_key)

    vector["inputs"]["checkpoint"] = {
        "state": "RESOLVED_ALLOW",
        "resolver_principal_kind": "human",
    }

    result = conf.evaluate_conformance_vector(vector, public_key)

    assert result.decision == "ALLOW"


def test_only_token_signer_key_revoked_hits_token_revocation_branch():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    vector = _add_token(
        _base_vector(private_key),
        private_key,
        signer_key_id="revoked-token-key",
    )
    vector["policy_context"]["revoked_keys"] = ["revoked-token-key"]

    result = conf.evaluate_conformance_vector(vector, public_key)

    assert result.decision == "DENY"
    assert result.reason_codes == ("KEY_REVOKED",)


def test_trusted_envelope_and_token_keys_continue_past_trust_gate():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    vector = _add_token(_base_vector(private_key), private_key)

    vector["policy_context"]["trusted_keys"] = ["key-ed25519-test-001"]

    result = conf.evaluate_conformance_vector(vector, public_key)

    assert result.decision == "ALLOW"
    assert result.envelope_signature_valid is True
    assert result.token_signature_valid is True


# ---------------------------------------------------------------------------
# langchain_guard.py: optional LangChain dependency fallback.
# Covers line 66 -> exit.
# ---------------------------------------------------------------------------

def test_on_llm_end_returns_immediately_when_llmresult_unavailable(monkeypatch):
    monkeypatch.setattr(langchain_guard, "LLMResult", None)

    # __new__ is enough: the early-return branch must execute before
    # any instance attributes are accessed.
    callback = AgencyGuardCallback.__new__(AgencyGuardCallback)

    assert callback.on_llm_end(
        object(),
        run_id="run-1",
    ) is None


# ---------------------------------------------------------------------------
# safe_harbor.py: empty existing file and missing verification file.
# Covers 47->exit and 88->exit.
# ---------------------------------------------------------------------------

def test_safe_harbor_existing_empty_file_uses_genesis_hash(tmp_path: Path):
    ledger_path = tmp_path / "empty-ledger.jsonl"
    ledger_path.touch()

    ledger = SafeHarborLedger(str(ledger_path))

    assert ledger.last_hash == ledger.GENESIS_HASH


def test_safe_harbor_verify_integrity_missing_file_is_true(tmp_path: Path):
    ledger_path = tmp_path / "does-not-exist.jsonl"
    ledger = SafeHarborLedger(str(ledger_path))

    # Constructor already sees a missing file; verify_integrity must
    # independently take its own missing-file fast path.
    assert not ledger_path.exists()
    assert ledger.verify_integrity() is True

def test_empty_checkpoint_state_continues_to_gate_2():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    vector = _base_vector(private_key)

    vector["inputs"]["checkpoint"] = {
        "state": "",
    }

    result = conf.evaluate_conformance_vector(vector, public_key)

    assert result.decision == "ALLOW"