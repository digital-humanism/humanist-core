"""Differential conformance against normative HACP v0.9.2 vectors."""
from __future__ import annotations

import pytest

from humanist_core.hacp.conformance import evaluate_conformance_vector

from .helpers import (
    canonicalize_envelope_for_verify,
    canonicalize_token_for_verify,
    compute_action_hash,
    verify_signature,
)


def test_vector_inventory(conformance_vectors):
    """Pinned HACP v0.9.2 baseline contains exactly 38 vectors."""
    assert len(conformance_vectors) == 38


def test_conformance_vector(conformance_vector, test_public_key):
    """Run one normative HACP conformance vector."""
    if conformance_vector is None:
        pytest.skip("conformance vectors unavailable")

    vector = conformance_vector

    # Only explicitly marked draft vectors are skipped.
    # Missing draft_mode means normal/baked vector.
    if vector.get("draft_mode") is True:
        pytest.skip("draft vector")

    test_id = vector["test_id"]
    inputs = vector["inputs"]
    expected = vector["expected"]

    envelope = inputs["intent_envelope"]
    action = inputs["proposed_action"]
    token = inputs.get("decision_token")

    result = evaluate_conformance_vector(
        vector,
        test_public_key,
    )

    # ------------------------------------------------------------------
    # 1. Normative decision parity
    # ------------------------------------------------------------------
    assert result.decision == expected["outcome"], (
        f"{test_id}: outcome mismatch\n"
        f"expected: {expected['outcome']}\n"
        f"computed: {result.decision}\n"
        f"reasons:  {result.reason_codes}"
    )

    # ------------------------------------------------------------------
    # 2. Action hash parity
    # ------------------------------------------------------------------
    independently_computed_hash = compute_action_hash(action)

    assert result.action_hash == independently_computed_hash, (
        f"{test_id}: evaluator/helper action hash mismatch\n"
        f"evaluator: {result.action_hash}\n"
        f"helper:    {independently_computed_hash}"
    )

    expected_hash = expected.get("action_hash")

    if expected_hash is not None:
        assert result.action_hash == expected_hash, (
            f"{test_id}: normative action hash mismatch\n"
            f"expected: {expected_hash}\n"
            f"computed: {result.action_hash}\n"
            f"canonical action: {result.canonical_action!r}"
        )

    # ------------------------------------------------------------------
    # 3. Normative reason-code parity
    # ------------------------------------------------------------------
    expected_reason = expected.get("reason_code")
    expected_reasons = expected.get("reason_codes")

    if expected_reason is not None:
        assert expected_reason in result.reason_codes, (
            f"{test_id}: reason mismatch\n"
            f"expected: {expected_reason}\n"
            f"computed: {result.reason_codes}"
        )

    if expected_reasons:
        assert any(
            reason in result.reason_codes
            for reason in expected_reasons
        ), (
            f"{test_id}: reason mismatch\n"
            f"expected one of: {expected_reasons}\n"
            f"computed:        {result.reason_codes}"
        )

    # ------------------------------------------------------------------
    # 4. Golden cross-language crypto parity
    # ------------------------------------------------------------------
    if vector.get("type") == "golden":
        envelope_bytes = canonicalize_envelope_for_verify(envelope)

        assert envelope_bytes == result.canonical_envelope, (
            f"{test_id}: envelope canonical-byte mismatch"
        )

        assert verify_signature(
            envelope_bytes,
            envelope["signature"],
            test_public_key,
        ), (
            f"{test_id}: envelope Ed25519 verification failed"
        )

        if token is not None:
            assert token["action_hash"] == independently_computed_hash, (
                f"{test_id}: token action_hash is not bound "
                "to canonical proposed_action"
            )

            token_bytes = canonicalize_token_for_verify(token)

            assert token_bytes == result.canonical_token, (
                f"{test_id}: token canonical-byte mismatch"
            )

            assert verify_signature(
                token_bytes,
                token["signature"],
                test_public_key,
            ), (
                f"{test_id}: token Ed25519 verification failed"
            )