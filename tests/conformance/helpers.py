"""Helpers for HACP differential conformance tests."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature

from humanist_core.hacp.crypto import (
    b64url_decode,
    canonicalize_json,
    hash_sha256,
)


def without_signature(value: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if k != "signature"}


def canonicalize_envelope_for_verify(envelope: Mapping[str, Any]) -> bytes:
    return canonicalize_json(without_signature(envelope))


def canonicalize_token_for_verify(token: Mapping[str, Any]) -> bytes:
    return canonicalize_json(without_signature(token))


def canonicalize_provenance_for_verify(event: Mapping[str, Any]) -> bytes:
    return canonicalize_json(without_signature(event))


def verify_signature(canonical_bytes, signature_b64url, public_key) -> bool:
    try:
        sig_bytes = b64url_decode(signature_b64url)
        public_key.verify(sig_bytes, canonical_bytes)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def compute_action_hash(proposed_action: Mapping[str, Any]) -> str:
    canonical = canonicalize_json(dict(proposed_action))
    return hash_sha256(canonical)


def reordered_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in reversed(list(value.keys())):
        item = value[key]
        if isinstance(item, dict):
            item = reordered_dict(item)
        elif isinstance(item, list):
            item = [
                reordered_dict(v) if isinstance(v, dict) else deepcopy(v)
                for v in item
            ]
        result[key] = item
    return result
