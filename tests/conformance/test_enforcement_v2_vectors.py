"""HACP-Enforcement revision 2 Family-A conformance against HC2-55."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from humanist_core.hacp.conformance_enforcement_v2 import (
    evaluate_enforcement_v2_vector,
)


def _resolve_spec_repo() -> Path:
    env_path = os.environ.get("HACP_SPEC_REPO")
    if env_path:
        return Path(env_path).resolve()

    repo_root = Path(__file__).resolve().parents[2]
    return (repo_root.parent / "hacp-spec").resolve()


def _load_hc2_vectors() -> list[dict]:
    vectors_dir = _resolve_spec_repo() / "vectors" / "enforcement-v2"

    if not vectors_dir.exists():
        return []

    vectors: list[dict] = []

    for path in sorted(vectors_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))

        if "test_id" not in data:
            continue

        vectors.append(data)

    return vectors


HC2_VECTORS = _load_hc2_vectors()


def test_hc2_vector_inventory():
    """The active Enforcement revision-2 evidence directory has 55 vectors."""
    if not HC2_VECTORS:
        pytest.skip(
            "HACP Enforcement vectors unavailable; set HACP_SPEC_REPO "
            "or clone hacp-spec beside humanist-core"
        )

    assert len(HC2_VECTORS) == 55

    test_ids = [vector["test_id"] for vector in HC2_VECTORS]
    assert len(test_ids) == len(set(test_ids)), "duplicate HC2 test_id detected"


@pytest.mark.parametrize(
    "hc2_vector",
    HC2_VECTORS,
    ids=[vector["test_id"] for vector in HC2_VECTORS],
)
def test_enforcement_v2_family_a_vector(hc2_vector, test_public_key):
    """Run one HC2-55 Family-A vector."""
    result = evaluate_enforcement_v2_vector(
        hc2_vector,
        test_public_key,
    )

    expected = hc2_vector["expected"]

    assert result.decision == expected["outcome"], (
        f"{hc2_vector['test_id']}: outcome mismatch\n"
        f"expected: {expected['outcome']}\n"
        f"computed: {result.decision}\n"
        f"reasons:  {result.reason_codes}"
    )

    expected_reasons = expected.get("reason_codes", [])

    if "SCOPE_EXCEEDED" in expected_reasons:
        assert "SCOPE_EXCEEDED" in result.reason_codes, (
            f"{hc2_vector['test_id']}: missing HC2 scope reason\n"
            f"computed: {result.reason_codes}"
        )

def _historical_allow_result(test_public_key):
    """Build a real Core ALLOW result for successor guard-path tests."""
    from humanist_core.hacp.conformance import evaluate_conformance_vector

    allow_vector = next(
        vector
        for vector in HC2_VECTORS
        if vector["expected"]["outcome"] == "ALLOW"
    )

    result = evaluate_conformance_vector(
        allow_vector,
        test_public_key,
    )

    assert result.decision == "ALLOW"
    return result


def test_enforcement_v2_preserves_non_allow_core_result(
    monkeypatch,
    test_public_key,
):
    """HC2 processing must not override a pre-existing Core DENY."""
    from dataclasses import replace

    import humanist_core.hacp.conformance_enforcement_v2 as enforcement_v2

    allow_result = _historical_allow_result(test_public_key)
    deny_result = replace(allow_result, decision="DENY")

    monkeypatch.setattr(
        enforcement_v2,
        "evaluate_conformance_vector",
        lambda vector, public_key: deny_result,
    )

    result = enforcement_v2.evaluate_enforcement_v2_vector(
        {},
        test_public_key,
    )

    assert result is deny_result
    assert result.decision == "DENY"


@pytest.mark.parametrize(
    "vector",
    [
        {"inputs": None},
        {
            "inputs": {
                "http_request": None,
            }
        },
        {
            "inputs": {
                "http_request": {},
                "decision_token": None,
            }
        },
        {
            "inputs": {
                "http_request": {},
                "decision_token": {
                    "constraints": None,
                },
            }
        },
        {
            "inputs": {
                "http_request": {},
                "decision_token": {
                    "constraints": {
                        "path": None,
                    },
                },
            }
        },
        {
            "inputs": {
                "http_request": {
                    "request_target": None,
                },
                "decision_token": {
                    "constraints": {
                        "path": "/",
                    },
                },
            }
        },
    ],
    ids=[
        "inputs-not-mapping",
        "http-request-not-mapping",
        "decision-token-not-mapping",
        "constraints-not-mapping",
        "constraint-path-not-string",
        "request-target-not-string",
    ],
)
def test_enforcement_v2_defensive_hc2_input_guards(
    vector,
    monkeypatch,
    test_public_key,
):
    """Malformed HC2-only structures preserve the successful Core result."""
    import humanist_core.hacp.conformance_enforcement_v2 as enforcement_v2

    allow_result = _historical_allow_result(test_public_key)

    monkeypatch.setattr(
        enforcement_v2,
        "evaluate_conformance_vector",
        lambda candidate, public_key: allow_result,
    )

    result = enforcement_v2.evaluate_enforcement_v2_vector(
        vector,
        test_public_key,
    )

    assert result is allow_result
    assert result.decision == "ALLOW"
