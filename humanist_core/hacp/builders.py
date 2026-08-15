"""Fluent builders for HACP Intent Envelopes and Decision Tokens."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union

from .models import (
    Scope,
    AutonomyBudget,
    IntentEnvelope,
    ProposedAction,
    HTTPProposedAction,
    Constraints,
    DecisionToken,
)
from .crypto import sign, b64url_encode, hash_action, hash_sha256, generate_key_id, canonicalize_json
from .exceptions import SchemaValidationError


def _as_list(value: Union[str, Sequence[str], None], default: str) -> List[str]:
    if value is None:
        return [default]
    if isinstance(value, str):
        return [value]
    return list(value)


@dataclass
class SignedIntentEnvelope:
    envelope: IntentEnvelope
    signature: str

    def to_dict(self) -> dict:
        payload = self.envelope.to_dict()
        payload["signature"] = self.signature
        return payload

    def to_b64url(self) -> str:
        return b64url_encode(canonicalize_json(self.to_dict()))


@dataclass
class SignedDecisionToken:
    token: DecisionToken
    signature: str

    def to_dict(self) -> dict:
        data = self.token.to_dict()
        data["signature"] = self.signature
        return data

    def to_b64url(self) -> str:
        return b64url_encode(canonicalize_json(self.to_dict()))


class EnvelopeBuilder:
    def __init__(self):
        self._hacp_version = "0.9"
        self._principal: Optional[str] = None
        self._principal_kind = "system"
        self._intent_statement: Optional[str] = None
        self._verbs: List[str] = []
        self._resource_classes: List[str] = []
        self._audiences: List[str] = []
        self._reversibility: List[str] = ["reversible"]
        self._externality: List[str] = ["internal"]
        self._data_classes: List[str] = []
        self._autonomy_budget: Optional[AutonomyBudget] = None
        self._issued_at: Optional[int] = None
        self._expires_at: Optional[int] = None
        self._signer_key_id: Optional[str] = None
        self._envelope_id: Optional[str] = None
        self._parent_envelope_id: Optional[str] = None

    def hacp_version(self, version: str) -> "EnvelopeBuilder":
        self._hacp_version = version
        return self

    def principal(self, principal: str) -> "EnvelopeBuilder":
        self._principal = principal
        return self

    def principal_kind(self, kind: str) -> "EnvelopeBuilder":
        if kind not in ("human", "system", "delegated"):
            raise SchemaValidationError(f"Invalid principal_kind: {kind}")
        self._principal_kind = kind
        return self

    def intent_statement(self, statement: str) -> "EnvelopeBuilder":
        self._intent_statement = statement
        return self

    def scope(
        self,
        verbs: List[str],
        resource_classes: List[str],
        audiences: List[str],
        reversibility: Union[str, Sequence[str]] = "reversible",
        externality: Union[str, Sequence[str]] = "internal",
        data_classes: Optional[List[str]] = None,
    ) -> "EnvelopeBuilder":
        self._verbs = list(verbs)
        self._resource_classes = list(resource_classes)
        self._audiences = list(audiences)
        self._reversibility = _as_list(reversibility, "reversible")
        self._externality = _as_list(externality, "internal")
        self._data_classes = list(data_classes or [])
        return self

    def autonomy_budget(self, max_actions: int, expires_at: int) -> "EnvelopeBuilder":
        self._autonomy_budget = AutonomyBudget(max_actions=max_actions, expires_at=expires_at)
        return self

    def issued_at(self, ts: int) -> "EnvelopeBuilder":
        self._issued_at = ts
        return self

    def expires_at(self, ts: int) -> "EnvelopeBuilder":
        self._expires_at = ts
        return self

    def signer_key_id(self, key_id: str) -> "EnvelopeBuilder":
        self._signer_key_id = key_id
        return self

    def envelope_id(self, env_id: str) -> "EnvelopeBuilder":
        self._envelope_id = env_id
        return self

    def parent_envelope_id(self, env_id: str) -> "EnvelopeBuilder":
        self._parent_envelope_id = env_id
        return self

    def build_unsigned(self) -> IntentEnvelope:
        if not self._principal:
            raise SchemaValidationError("principal is required")
        if self._issued_at is None:
            self._issued_at = int(time.time())
        if self._expires_at is None:
            self._expires_at = self._issued_at + 3600
        if self._intent_statement is None:
            self._intent_statement = f"HACP intent for {self._principal}"
        if self._signer_key_id is None:
            self._signer_key_id = generate_key_id()
        if self._envelope_id is None:
            self._envelope_id = str(uuid.uuid4())

        return IntentEnvelope(
            hacp_version=self._hacp_version,
            envelope_id=self._envelope_id,
            principal=self._principal,
            principal_kind=self._principal_kind,
            intent_statement=self._intent_statement,
            scope=Scope(
                verbs=self._verbs,
                resource_classes=self._resource_classes,
                audiences=self._audiences,
                reversibility=self._reversibility,
                externality=self._externality,
                data_classes=self._data_classes,
            ),
            autonomy_budget=self._autonomy_budget,
            signer_key_id=self._signer_key_id,
            issued_at=self._issued_at,
            expires_at=self._expires_at,
            parent_envelope_id=self._parent_envelope_id,
        )

    def canonicalize(self) -> bytes:
        return canonicalize_json(self.build_unsigned().to_dict())

    def sign(self, private_key) -> SignedIntentEnvelope:
        envelope = self.build_unsigned()
        signature = b64url_encode(sign(canonicalize_json(envelope.to_dict()), private_key))
        return SignedIntentEnvelope(envelope=envelope, signature=signature)


class TokenBuilder:
    """Builder for a HACP v0.9 DecisionToken."""

    def __init__(self):
        self._envelope: Optional[IntentEnvelope] = None
        self._proposed_action: Optional[Union[ProposedAction, HTTPProposedAction]] = None
        self._constraints: Optional[Constraints] = None
        self._decision = "ALLOW"
        self._policy_digest = ""
        self._issued_at: Optional[int] = None
        self._expires_at: Optional[int] = None
        self._token_id: Optional[str] = None
        self._signer_key_id: Optional[str] = None

    def envelope(self, envelope: IntentEnvelope) -> "TokenBuilder":
        self._envelope = envelope
        if self._expires_at is None:
            self._expires_at = envelope.expires_at
        if self._signer_key_id is None:
            self._signer_key_id = envelope.signer_key_id
        return self

    def proposed_action(
        self,
        verb: str,
        resource_class: str,
        resource_id: str,
        audience: str,
        data_class: str,
    ) -> "TokenBuilder":
        self._proposed_action = ProposedAction(
            verb=verb,
            resource_class=resource_class,
            resource_id=resource_id,
            audience=audience,
            data_class=data_class,
        )
        return self

    def http_action(
        self,
        method: str,
        path: str,
        body: bytes = b"",
        *,
        resource_class: Optional[str] = None,
        audience: Optional[str] = None,
        reversibility: Optional[str] = None,
        externality: Optional[str] = None,
        data_class: Optional[str] = None,
    ) -> "TokenBuilder":
        """Bind the token to the exact HTTP ProposedAction used by hacp-sidecar.

        hacp-sidecar derives the action from the HTTP method/path, the granted
        envelope scope, and SHA-256 of the request body.  For a GET with an
        empty body this matches the benchmark/conformance token generator.
        """
        if self._envelope is None:
            raise SchemaValidationError(
                "envelope must be set before http_action()"
            )

        scope = self._envelope.scope

        def first(values, name: str) -> str:
            if not values:
                raise SchemaValidationError(
                    f"envelope scope.{name} must contain at least one value"
                )
            return values[0]

        method_upper = method.upper()
        verb_map = {
            "GET": "read",
            "HEAD": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        verb = verb_map.get(method_upper, method_upper.lower())

        self._proposed_action = HTTPProposedAction(
            hacp_version=self._envelope.hacp_version,
            verb=verb,
            resource_class=resource_class or first(
                scope.resource_classes, "resource_classes"
            ),
            resource_id=path,
            audience=audience or first(scope.audiences, "audiences"),
            reversibility=reversibility or first(
                scope.reversibility, "reversibility"
            ),
            externality=externality or first(
                scope.externality, "externality"
            ),
            data_class=data_class or first(
                scope.data_classes, "data_classes"
            ),
            payload_hash=hash_sha256(body),
        )
        return self

    def constraints(
        self,
        method: Optional[str] = None,
        path: Optional[str] = None,
        max_uses: Optional[int] = None,
        tool_name: Optional[str] = None,
        payload_hash: Optional[str] = None,
    ) -> "TokenBuilder":
        self._constraints = Constraints(
            method=method,
            path=path,
            max_uses=max_uses,
            tool_name=tool_name,
            payload_hash=payload_hash,
        )
        return self

    def decision(self, decision: str) -> "TokenBuilder":
        if decision not in ("ALLOW", "CHECKPOINT", "DENY"):
            raise SchemaValidationError(f"Invalid decision: {decision}")
        self._decision = decision
        return self

    def policy_digest(self, digest: str) -> "TokenBuilder":
        self._policy_digest = digest
        return self

    def issued_at(self, ts: int) -> "TokenBuilder":
        self._issued_at = ts
        return self

    def expires_at(self, ts: int) -> "TokenBuilder":
        self._expires_at = ts
        return self

    def token_id(self, token_id: str) -> "TokenBuilder":
        self._token_id = token_id
        return self

    def signer_key_id(self, key_id: str) -> "TokenBuilder":
        self._signer_key_id = key_id
        return self

    def build_unsigned(self) -> DecisionToken:
        if self._envelope is None:
            raise SchemaValidationError("envelope is required")
        if self._proposed_action is None:
            raise SchemaValidationError("proposed_action is required")

        now = int(time.time())
        if self._issued_at is None:
            self._issued_at = now
        if self._expires_at is None:
            self._expires_at = self._envelope.expires_at
        if self._token_id is None:
            self._token_id = str(uuid.uuid4())
        if self._signer_key_id is None:
            self._signer_key_id = self._envelope.signer_key_id
        if self._envelope.envelope_id is None:
            raise SchemaValidationError("envelope.envelope_id is required")

        return DecisionToken(
            hacp_version=self._envelope.hacp_version,
            token_id=self._token_id,
            envelope_id=self._envelope.envelope_id,
            action_hash=hash_action(self._proposed_action.to_dict()),
            policy_digest=self._policy_digest,
            principal=self._envelope.principal,
            signer_key_id=self._signer_key_id,
            issued_at=self._issued_at,
            expires_at=self._expires_at,
            decision=self._decision,
            constraints=self._constraints,
        )

    def canonicalize(self) -> bytes:
        return canonicalize_json(self.build_unsigned().to_dict())

    def sign(self, private_key) -> SignedDecisionToken:
        token = self.build_unsigned()
        signature = b64url_encode(sign(canonicalize_json(token.to_dict()), private_key))
        return SignedDecisionToken(token=token, signature=signature)
