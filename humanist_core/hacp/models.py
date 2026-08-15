"""Data models for the HACP Sidecar SDK.

Wire serialization follows the HACP v0.9.x structures used by hacp-sidecar.
JCS canonicalization is performed by builders before Ed25519 signing.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Scope:
    """Allowed operations for an agent."""
    verbs: List[str]
    resource_classes: List[str]
    audiences: List[str]
    reversibility: List[str]
    externality: List[str]
    data_classes: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AutonomyBudget:
    """Optional autonomous-execution budget."""
    max_actions: int
    expires_at: int
    used_actions: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IntentEnvelope:
    """HACP v0.9 Intent Envelope."""
    principal: str
    principal_kind: str
    scope: Scope
    signer_key_id: str
    issued_at: int
    expires_at: int
    envelope_id: Optional[str] = None

    hacp_version: str = "0.9"
    intent_statement: str = ""
    autonomy_budget: Optional[AutonomyBudget] = None
    parent_envelope_id: Optional[str] = None

    def to_dict(self, include_signature: bool = False) -> dict:
        data = {
            "hacp_version": self.hacp_version,
            "envelope_id": self.envelope_id,
            "principal": self.principal,
            "principal_kind": self.principal_kind,
            "intent_statement": self.intent_statement,
            "scope": self.scope.to_dict(),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "signer_key_id": self.signer_key_id,
        }
        if self.parent_envelope_id is not None:
            data["parent_envelope_id"] = self.parent_envelope_id
        if self.autonomy_budget is not None:
            data["autonomy_budget"] = self.autonomy_budget.to_dict()
        return data


@dataclass
class ProposedAction:
    """Compact SDK representation of a proposed action."""
    verb: str
    resource_class: str
    resource_id: str
    audience: str
    data_class: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HTTPProposedAction:
    """HTTP-mode ProposedAction matching hacp-sidecar proxy synthesis.

    This is the object whose JCS SHA-256 is bound to DecisionToken.action_hash
    for HTTP proxy requests.
    """
    hacp_version: str
    verb: str
    resource_class: str
    resource_id: str
    audience: str
    reversibility: str
    externality: str
    data_class: str
    payload_hash: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Constraints:
    """Optional DecisionToken request constraints."""
    method: Optional[str] = None
    path: Optional[str] = None
    tool_name: Optional[str] = None
    payload_hash: Optional[str] = None
    max_uses: Optional[int] = None

    def to_dict(self) -> dict:
        # HACP optional constraint fields must be absent rather than null.
        return {
            key: value
            for key, value in {
                "method": self.method,
                "path": self.path,
                "tool_name": self.tool_name,
                "payload_hash": self.payload_hash,
                "max_uses": self.max_uses,
            }.items()
            if value is not None
        }


@dataclass
class DecisionToken:
    """HACP v0.9 Decision Token.

    Signature is detached by SignedDecisionToken and is therefore intentionally
    absent from this model's canonical payload.
    """
    hacp_version: str
    token_id: str
    envelope_id: str
    action_hash: str
    policy_digest: str
    principal: str
    signer_key_id: str
    issued_at: int
    expires_at: int
    decision: str
    constraints: Optional[Constraints] = None

    def to_dict(self, include_signature: bool = False) -> dict:
        data = {
            "hacp_version": self.hacp_version,
            "token_id": self.token_id,
            "envelope_id": self.envelope_id,
            "action_hash": self.action_hash,
            "policy_digest": self.policy_digest,
            "principal": self.principal,
            "signer_key_id": self.signer_key_id,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "decision": self.decision,
        }
        if self.constraints is not None:
            data["constraints"] = self.constraints.to_dict()
        return data
