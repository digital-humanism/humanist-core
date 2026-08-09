"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 1: Authority Core.
    Establishes explicit bounded authority and eliminates global
    approval state. See docs/ARCHITECTURE_v2.0.md, Section 27.1.
"""
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AgencyDecision(Enum):
    """Possible outcomes of an authorization evaluation."""
    ALLOW = "allow"                      # low risk, fully within current authority
    ALLOW_WITH_AUDIT = "allow_with_audit"  # authorized, but requires provenance
    CHECKPOINT = "checkpoint"            # meaningful human judgment required
    REAUTHORIZE = "reauthorize"          # action exceeds the Intent Envelope
    DENY = "deny"                        # violates a non-overridable constraint


@dataclass(frozen=True)
class IntentEnvelope:
    """
    A bounded representation of the authority granted by a human.
    The human authorizes a capability space, not a sentence.
    """
    actor_id: str
    objective: str
    operations: Tuple[str, ...]
    forbidden: Tuple[str, ...] = ()
    systems: Tuple[str, ...] = ()
    constraints: Dict[str, Any] = field(default_factory=dict)
    issued_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    signature: Optional[str] = None  # ed25519 in full v2.0 provenance

    def is_expired(self, now: float) -> bool:
        return self.expires_at is not None and now > self.expires_at


@dataclass(frozen=True)
class ProposedAction:
    """
    A meaningful action proposed by an autonomous system.
    NOTE: dimensions may be self-reported by the agent and are treated
    as untrusted input (hardened in Phase 2 — Semantic Delta Guard).
    """
    operation: str
    resource: str = ""
    system: str = ""
    audience: str = ""
    effect: str = ""
    quantity: Optional[int] = None


@dataclass(frozen=True)
class DecisionToken:
    """
    A narrowly scoped, short-lived capability produced by a human decision.
    Never a global flag: binds operation, resource, quantity and time.
    """
    permits: str
    resource: str
    actor_id: str
    parent_intent: str
    max_quantity: Optional[int] = None
    issued_at: float = field(default_factory=time.time)
    expires_in: float = 300.0
    nonce: str = field(default_factory=lambda: uuid.uuid4().hex)

    def is_valid(self, now: Optional[float] = None) -> bool:
        now = time.time() if now is None else now
        return now <= self.issued_at + self.expires_in

    def covers(self, action: ProposedAction) -> bool:
        if action.operation != self.permits:
            return False
        if self.resource and action.resource and action.resource != self.resource:
            return False
        if (
            self.max_quantity is not None
            and action.quantity is not None
            and action.quantity > self.max_quantity
        ):
            return False
        return True


class ScopeGuard:
    """
    Determines whether a proposed action remains inside the Intent
    Envelope. Deny-by-default on uncertainty: missing or ambiguous
    dimensions never expand authority.
    """

    EXTERNAL_EFFECTS = ("reputational", "financial", "legal")

    def evaluate(self, envelope: IntentEnvelope, action: ProposedAction,
                 now: float) -> AgencyDecision:
        # Authority itself may have expired.
        if envelope.is_expired(now):
            return AgencyDecision.REAUTHORIZE

        # Forbidden operations are non-overridable.
        if action.operation in envelope.forbidden:
            return AgencyDecision.DENY

        # Operation not granted by the envelope -> new authority required.
        if action.operation not in envelope.operations:
            return AgencyDecision.REAUTHORIZE

        # System boundary.
        if envelope.systems and action.system and action.system not in envelope.systems:
            return AgencyDecision.REAUTHORIZE

        # Inside the granted operation, but beyond a declared constraint:
        # a meaningful human decision is required.
        max_q = envelope.constraints.get("max_quantity")
        if max_q is not None and action.quantity is not None and action.quantity > max_q:
            return AgencyDecision.CHECKPOINT

        # Externality boundary: effect/audience shifts are security-relevant
        # even when the operation itself is granted.
        if action.effect in self.EXTERNAL_EFFECTS:
            return AgencyDecision.CHECKPOINT
        if action.audience and action.audience not in ("requester", "self"):
            return AgencyDecision.CHECKPOINT

        return AgencyDecision.ALLOW


class AgencyKernel:
    """
    Phase 1 Authority Core.
    Combines Scope Guard evaluation with bounded, expiring Decision
    Tokens. Execution depends on authority, not merely agent intention.
    """

    def __init__(self, audit_operations: Optional[set] = None):
        self.scope_guard = ScopeGuard()
        self.audit_operations = audit_operations or {"modify", "write"}
        self._tokens: List[DecisionToken] = []

    def authorize_intent(
        self,
        actor_id: str,
        objective: str,
        operations: Tuple[str, ...],
        forbidden: Tuple[str, ...] = (),
        systems: Tuple[str, ...] = (),
        constraints: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
        signature: Optional[str] = None,
    ) -> IntentEnvelope:
        return IntentEnvelope(
            actor_id=actor_id,
            objective=objective,
            operations=tuple(operations),
            forbidden=tuple(forbidden),
            systems=tuple(systems),
            constraints=constraints or {},
            expires_at=time.time() + ttl if ttl else None,
            signature=signature,
        )

    def issue_decision_token(
        self,
        envelope: IntentEnvelope,
        permits: str,
        resource: str,
        max_quantity: Optional[int] = None,
        expires_in: float = 300.0,
    ) -> DecisionToken:
        """Human checkpoint outcome: a bounded capability, not a boolean."""
        token = DecisionToken(
            permits=permits,
            resource=resource,
            actor_id=envelope.actor_id,
            parent_intent=envelope.objective,
            max_quantity=max_quantity,
            expires_in=expires_in,
        )
        self._tokens.append(token)
        return token

    def evaluate(self, envelope: IntentEnvelope, action: ProposedAction,
                 now: Optional[float] = None) -> AgencyDecision:
        now = time.time() if now is None else now

        # A fresh, covering Decision Token is bounded human authority.
        for token in self._tokens:
            if token.actor_id == envelope.actor_id and token.covers(action):
                if token.is_valid(now):
                    return AgencyDecision.ALLOW_WITH_AUDIT
                # Approval existed but expired: authority must be renewed.
                return AgencyDecision.REAUTHORIZE

        decision = self.scope_guard.evaluate(envelope, action, now)

        # Granted but consequential operations require stronger provenance.
        if decision == AgencyDecision.ALLOW and action.operation in self.audit_operations:
            return AgencyDecision.ALLOW_WITH_AUDIT

        return decision