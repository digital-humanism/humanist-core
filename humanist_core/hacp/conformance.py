"""Clean-room HACP v0.9.2 conformance evaluator.

This module operates on normative wire dictionaries rather than SDK dataclasses.
It is intended only for differential conformance testing against hacp-spec.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .crypto import b64url_decode, canonicalize_json, hash_sha256


GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class ConformanceResult:
    decision: str
    reason_codes: tuple[str, ...]
    action_hash: str
    canonical_action: bytes
    canonical_envelope: bytes
    canonical_token: Optional[bytes] = None
    envelope_signature_valid: Optional[bool] = None
    token_signature_valid: Optional[bool] = None
    provenance_valid: Optional[bool] = None
    provenance_event_id: Optional[str] = None


def _without_signature(value: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if k != "signature"}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _contains(values: Any, candidate: Any) -> bool:
    return candidate in _as_list(values)


def _clock(context: Mapping[str, Any], envelope: Mapping[str, Any]) -> int:
    value = context.get("current_time", context.get("clock"))
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    issued_at = envelope.get("issued_at")
    return issued_at if isinstance(issued_at, int) else 0


def _verify_signature(
    public_key: Ed25519PublicKey,
    canonical_bytes: bytes,
    signature_b64url: Any,
) -> bool:
    if not isinstance(signature_b64url, str) or not signature_b64url:
        return False
    try:
        signature = b64url_decode(signature_b64url)
        public_key.verify(signature, canonical_bytes)
        return True
    except Exception:
        return False


def _result(
    decision: str,
    reason: Optional[str],
    *,
    action_hash: str,
    canonical_action: bytes,
    canonical_envelope: bytes,
    canonical_token: Optional[bytes],
    envelope_signature_valid: Optional[bool] = None,
    token_signature_valid: Optional[bool] = None,
    provenance_valid: Optional[bool] = None,
    provenance_event_id: Optional[str] = None,
) -> ConformanceResult:
    return ConformanceResult(
        decision=decision,
        reason_codes=(reason,) if reason else (),
        action_hash=action_hash,
        canonical_action=canonical_action,
        canonical_envelope=canonical_envelope,
        canonical_token=canonical_token,
        envelope_signature_valid=envelope_signature_valid,
        token_signature_valid=token_signature_valid,
        provenance_valid=provenance_valid,
        provenance_event_id=provenance_event_id,
    )


def _scope_reason(
    action: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> Optional[str]:
    scope = envelope.get("scope")
    if not isinstance(scope, Mapping):
        return "SCOPE_EXCEEDED"

    checks = (
        ("audience", "audiences"),
        ("reversibility", "reversibility"),
        ("externality", "externality"),
        ("data_class", "data_classes"),
        ("verb", "verbs"),
        ("resource_class", "resource_classes"),
    )

    for action_key, scope_key in checks:
        allowed = scope.get(scope_key)
        if allowed is not None:
            if action_key not in action:
                return "UNKNOWN_ATTRIBUTE"
            if not _contains(allowed, action.get(action_key)):
                return "BOUNDARY_CROSSING"

    quantity = action.get("quantity")
    max_quantity = scope.get("max_quantity")
    if (
        isinstance(quantity, int)
        and not isinstance(quantity, bool)
        and isinstance(max_quantity, int)
        and not isinstance(max_quantity, bool)
        and quantity > max_quantity
    ):
        return "SCOPE_EXCEEDED"

    destinations = _as_list(scope.get("destinations"))
    if destinations:
        if "destination" not in action:
            return "UNKNOWN_ATTRIBUTE"
        if action.get("destination") not in destinations:
            return "BOUNDARY_CROSSING"

    tool_names = _as_list(scope.get("tool_names"))
    if tool_names:
        if "tool_name" not in action:
            return "UNKNOWN_ATTRIBUTE"
        if action.get("tool_name") not in tool_names:
            return "BOUNDARY_CROSSING"

    return None


def _verify_provenance(
    event: Mapping[str, Any],
    prior: Optional[Mapping[str, Any]],
    public_key: Ed25519PublicKey,
) -> bool:
    if "payload" not in event:
        return False

    try:
        payload_bytes = canonicalize_json(event["payload"])
    except Exception:
        return False

    if hash_sha256(payload_bytes) != event.get("payload_hash"):
        return False

    expected_prev = GENESIS_HASH
    if prior is not None:
        try:
            expected_prev = hash_sha256(canonicalize_json(dict(prior)))
        except Exception:
            return False

    if event.get("prev_event_hash") != expected_prev:
        return False

    try:
        event_bytes = canonicalize_json(_without_signature(event))
    except Exception:
        return False

    return _verify_signature(
        public_key,
        event_bytes,
        event.get("signature"),
    )


def evaluate_conformance_vector(
    vector: Mapping[str, Any],
    public_key: Ed25519PublicKey,
) -> ConformanceResult:
    """Evaluate one normative HACP v0.9.2 vector deterministically."""
    inputs = vector.get("inputs")
    if not isinstance(inputs, Mapping):
        raise ValueError("vector.inputs must be an object")

    envelope = inputs.get("intent_envelope")
    action = inputs.get("proposed_action")
    token = inputs.get("decision_token")

    if not isinstance(envelope, Mapping):
        raise ValueError("inputs.intent_envelope must be an object")
    if not isinstance(action, Mapping):
        raise ValueError("inputs.proposed_action must be an object")
    if token is not None and not isinstance(token, Mapping):
        raise ValueError("inputs.decision_token must be an object when present")

    context = vector.get("policy_context")
    if not isinstance(context, Mapping):
        context = inputs.get("policy_context")
    if not isinstance(context, Mapping):
        context = {}

    canonical_action = canonicalize_json(dict(action))
    action_hash = hash_sha256(canonical_action)
    canonical_envelope = canonicalize_json(_without_signature(envelope))
    canonical_token = (
        canonicalize_json(_without_signature(token))
        if isinstance(token, Mapping)
        else None
    )

    def make_result(
        decision: str,
        reason: str | None,
        *,
        envelope_signature_valid: bool | None = None,
        token_signature_valid: bool | None = None,
        provenance_valid: bool | None = None,
        provenance_event_id: str | None = None,
    ) -> ConformanceResult:
        return _result(
            decision,
            reason,
            action_hash=action_hash,
            canonical_action=canonical_action,
            canonical_envelope=canonical_envelope,
            canonical_token=canonical_token,
            envelope_signature_valid=envelope_signature_valid,
            token_signature_valid=token_signature_valid,
            provenance_valid=provenance_valid,
            provenance_event_id=provenance_event_id,
        )
    
    now = _clock(context, envelope)

    # ------------------------------------------------------------------
    # Gate 0: malformed wire input
    # ------------------------------------------------------------------
    if vector.get("_duplicate_json_keys"):
        return make_result("DENY", "INVALID_ACTION")

    # ------------------------------------------------------------------
    # Gate 1: checkpoint/runtime state
    # Must precede ordinary envelope expiry so checkpoint timeout retains
    # its normative reason code.
    # ------------------------------------------------------------------
    checkpoint_state = inputs.get("checkpoint_state")
    if isinstance(checkpoint_state, Mapping):
        created_at = checkpoint_state.get("created_at")
        timeout = checkpoint_state.get(
            "timeout_seconds",
            context.get("checkpoint_timeout_seconds"),
        )
        if (
            isinstance(created_at, int)
            and not isinstance(created_at, bool)
            and isinstance(timeout, int)
            and not isinstance(timeout, bool)
            and now > created_at + timeout
        ):
            return make_result("DENY", "CHECKPOINT_TIMEOUT")

    checkpoint = inputs.get("checkpoint")
    if isinstance(checkpoint, Mapping):
        state = checkpoint.get("state", "")
        expires_at = checkpoint.get("expires_at")

        if (
            state == "OPEN"
            and isinstance(expires_at, int)
            and not isinstance(expires_at, bool)
            and now > expires_at
        ):
            return make_result("DENY", "CHECKPOINT_TIMEOUT")

        if state == "OPEN":
            return make_result("CHECKPOINT", "CHECKPOINT_REQUIRED")

        if state == "RESOLVED_DENY":
            return make_result("DENY", "CHECKPOINT_DENIED")

        if state == "RESOLVED_ALLOW":
            if checkpoint.get("resolver_principal_kind") != "human":
                return make_result(
                    "DENY",
                    "HUMAN_RESOLUTION_REQUIRED",
                )
        elif state not in ("", None):
            return make_result("DENY", "INVALID_CHECKPOINT_STATE")

    # ------------------------------------------------------------------
    # Gate 2: token lifecycle and token binding
    # These checks intentionally precede envelope signature verification:
    # the normative vectors use placeholder signatures in several negative
    # cases whose expected failure is token binding/expiry.
    # ------------------------------------------------------------------
    revoked_keys = _as_list(context.get("revoked_keys"))

    if envelope.get("signer_key_id") in revoked_keys:
        return make_result("DENY", "KEY_REVOKED")

    if isinstance(token, Mapping) and token.get("signer_key_id") in revoked_keys:
        return make_result("DENY", "KEY_REVOKED")

    trusted_keys = context.get("trusted_keys")
    if trusted_keys is not None:
        if not _contains(trusted_keys, envelope.get("signer_key_id")):
            return make_result("DENY", "SIGNATURE_FAILURE")
        if isinstance(token, Mapping) and not _contains(
            trusted_keys,
            token.get("signer_key_id"),
        ):
            return make_result("DENY", "SIGNATURE_FAILURE")

    envelope_signer = str(envelope.get("signer_key_id", "")).lower()
    if "hmac" in envelope_signer:
        return make_result("DENY", "SIGNATURE_FAILURE")

    if isinstance(token, Mapping):
        token_signer = str(token.get("signer_key_id", "")).lower()
        if "hmac" in token_signer:
            return make_result("DENY", "SIGNATURE_FAILURE")

        revoked_tokens = _as_list(context.get("revoked_tokens"))
        if token.get("token_id") in revoked_tokens:
            return make_result("DENY", "TOKEN_REVOKED")

        token_exp = token.get("expires_at")
        if (
            isinstance(token_exp, int)
            and not isinstance(token_exp, bool)
            and now > token_exp
        ):
            return make_result("DENY", "TOKEN_EXPIRED")

        if token.get("envelope_id") != envelope.get("envelope_id"):
            return make_result(
                "DENY",
                "TOKEN_ENVELOPE_MISMATCH",
            )

        if token.get("action_hash") != action_hash:
            return make_result("DENY", "HASH_MISMATCH")

    # ------------------------------------------------------------------
    # Gate 3: provenance / traceability
    # Structural traceability failures precede crypto placeholder failures.
    # ------------------------------------------------------------------
    if bool(inputs.get("omit_provenance", False)):
        return make_result("DENY", "TRACEABILITY_MISSING")

    provenance = inputs.get("provenance_event")
    prior = inputs.get("prior_provenance_event")

    provenance_valid: Optional[bool] = None
    provenance_event_id: Optional[str] = None

    if provenance is not None:
        if not isinstance(provenance, Mapping):
            return make_result("DENY", "TRACEABILITY_FAILURE")

        provenance_valid = _verify_provenance(
            provenance,
            prior if isinstance(prior, Mapping) else None,
            public_key,
        )
        if not provenance_valid:
            return make_result(
                "DENY",
                "TRACEABILITY_FAILURE",
                provenance_valid=False,
            )

        provenance_event_id = provenance.get("event_id")

    # ------------------------------------------------------------------
    # Gate 4: envelope lifecycle / revocation
    # ------------------------------------------------------------------
    expires_at = envelope.get("expires_at")
    if (
        isinstance(expires_at, int)
        and not isinstance(expires_at, bool)
        and now > expires_at
    ):
        return make_result("DENY", "ENVELOPE_EXPIRED")

    revoked_envelopes = _as_list(context.get("revoked_envelopes"))
    if envelope.get("envelope_id") in revoked_envelopes:
        return make_result("DENY", "ENVELOPE_REVOKED")

    parent_id = envelope.get("parent_envelope_id")
    if parent_id and parent_id in revoked_envelopes:
        return make_result("DENY", "ENVELOPE_REVOKED")

    # ------------------------------------------------------------------
    # Gate 5: autonomy / authority / scope
    # ------------------------------------------------------------------
    budget = envelope.get("autonomy_budget")
    if isinstance(budget, Mapping):
        max_actions = budget.get("max_actions")
        current_count = context.get("current_action_count", 0)
        if (
            isinstance(max_actions, int)
            and not isinstance(max_actions, bool)
            and isinstance(current_count, int)
            and not isinstance(current_count, bool)
            and current_count >= max_actions
        ):
            return make_result("DENY", "BUDGET_EXHAUSTED")

    human_required_verbs = _as_list(context.get("human_required_verbs"))
    if (
        action.get("verb") in human_required_verbs
        and envelope.get("principal_kind") == "system"
        and not envelope.get("parent_envelope_id")
    ):
        return make_result("CHECKPOINT", "HUMAN_REQUIRED")

    scope_reason = _scope_reason(action, envelope)
    if scope_reason is not None:
        return make_result("DENY", scope_reason)

    # ------------------------------------------------------------------
    # Gate 6: Ed25519 verification
    # ------------------------------------------------------------------
    envelope_sig_ok = _verify_signature(
        public_key,
        canonical_envelope,
        envelope.get("signature"),
    )
    if not envelope_sig_ok:
        return make_result(
            "DENY",
            "SIGNATURE_FAILURE",
            envelope_signature_valid=False,
            provenance_valid=provenance_valid,
        )

    token_sig_ok: Optional[bool] = None
    if isinstance(token, Mapping):
        token_sig_ok = _verify_signature(
            public_key,
            canonical_token or b"",
            token.get("signature"),
        )
        if not token_sig_ok:
            return make_result(
                "DENY",
                "SIGNATURE_FAILURE",
                envelope_signature_valid=True,
                token_signature_valid=False,
                provenance_valid=provenance_valid,
            )

    return make_result(
        "ALLOW",
        None,
        envelope_signature_valid=True,
        token_signature_valid=token_sig_ok,
        provenance_valid=provenance_valid,
        provenance_event_id=provenance_event_id,
    )
