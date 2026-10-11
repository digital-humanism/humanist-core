"""HACP-Enforcement revision 2 Family-A conformance evaluator.

This module is an additive successor to the historical HACP-Core v0.9.2
conformance evaluator. It preserves the Core evaluator unchanged and adds
only the bounded HC2 HTTP request-target binding semantics.

This is a conformance/verification surface. It is not a production runtime
backend and does not redefine normative HACP semantics.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .conformance import ConformanceResult, evaluate_conformance_vector


def _is_hex_digit(value: str) -> bool:
    return value in "0123456789abcdefABCDEF"


def _normalize_hc2_request_target(target: str) -> str:
    """Normalize only hex case in valid percent-encoded triplets.

    Invalid or incomplete percent sequences are preserved literally.
    No URL decoding, query parsing, or broader URI normalization is applied.
    """
    result: list[str] = []
    index = 0

    while index < len(target):
        if (
            target[index] == "%"
            and index + 2 < len(target)
            and _is_hex_digit(target[index + 1])
            and _is_hex_digit(target[index + 2])
        ):
            result.append("%")
            result.append(target[index + 1].upper())
            result.append(target[index + 2].upper())
            index += 3
            continue

        result.append(target[index])
        index += 1

    return "".join(result)


def evaluate_enforcement_v2_vector(
    vector: Mapping[str, Any],
    public_key: Ed25519PublicKey,
) -> ConformanceResult:
    """Evaluate one HACP-Enforcement revision 2 Family-A vector.

    Historical HACP-Core behavior is evaluated first. HC2 request binding is
    applied only when the Core result is ALLOW.
    """
    result = evaluate_conformance_vector(vector, public_key)

    if result.decision != "ALLOW":
        return result

    inputs = vector.get("inputs")
    if not isinstance(inputs, Mapping):
        return result

    http_request = inputs.get("http_request")
    if not isinstance(http_request, Mapping):
        return result

    decision_token = inputs.get("decision_token")
    if not isinstance(decision_token, Mapping):
        return result

    constraints = decision_token.get("constraints")
    if not isinstance(constraints, Mapping):
        return result

    constraint_path = constraints.get("path")
    if not isinstance(constraint_path, str):
        return result

    request_target = http_request.get("request_target", "")
    if not isinstance(request_target, str):
        return result

    if (
        _normalize_hc2_request_target(request_target)
        != _normalize_hc2_request_target(constraint_path)
    ):
        return replace(
            result,
            decision="DENY",
            reason_codes=("SCOPE_EXCEEDED",),
        )

    return result
