"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 3: Cryptographic Provenance.
    Causal Provenance Graph with signed events, policy digests, and
    Decision Token verification. See docs/ARCHITECTURE_v2.0.md,
    Sections 14-15.

    NOTE: This reference implementation uses HMAC-SHA256 with a shared
    signing key (stdlib only). A production deployment should replace
    the signer with Ed25519 / TPM / HSM (see Future Work in ARCHITECTURE.md).
"""
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence


EVENT_TYPES = frozenset({
    "intent",          # human authorization envelope issued
    "tool_call",       # autonomous action proposed / executed
    "tool_result",     # tool execution result
    "semantic_delta",  # meaningful boundary detected
    "checkpoint",      # human judgment requested
    "decision",        # human decision produced a Decision Token
    "action",          # consequence-bearing action executed
    "policy_change",   # governing policy version changed
})


def _canonical_bytes(obj: Any) -> bytes:
    """Stable, ordered serialization for hashing / signing."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class ProvenanceEvent:
    """
    A node in the causal Provenance Graph.
    Each event links to its causal parents, carries a payload digest,
    a policy digest, and a cryptographic signature binding it to a
    signing authority.
    """
    event_id: str
    event_type: str
    parents: tuple  # tuple[str, ...] of event_ids
    actor: str
    payload_digest: str
    policy_digest: str
    timestamp: float = field(default_factory=time.time)
    # Free-form structured metadata (operation, resource, decision, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None

    def __post_init__(self):
        if self.event_type not in EVENT_TYPES:
            raise ValueError(f"Unknown event type: {self.event_type}")
        if not isinstance(self.parents, tuple):
            # frozen dataclass workaround: allow list at construction,
            # but store as tuple for hashability.
            object.__setattr__(self, "parents", tuple(self.parents))

    def signing_canonical(self) -> bytes:
        """Bytes that the signer signs. Excludes the signature itself."""
        return _canonical_bytes({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "parents": list(self.parents),
            "actor": self.actor,
            "payload_digest": self.payload_digest,
            "policy_digest": self.policy_digest,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        })


class EventSigner:
    """HMAC-SHA256 signer for ProvenanceEvents instances."""

    def __init__(self, key: bytes):
        if not key:
            raise ValueError("Signing key must not be empty")
        self._key = key

    def sign(self, event: ProvenanceEvent) -> str:
        return hmac.new(self._key, event.signing_canonical(),
                        hashlib.sha256).hexdigest()

    def verify(self, event: ProvenanceEvent) -> bool:
        if not event.signature:
            return False
        expected = self.sign(event)
        # Constant-time comparison to avoid timing leaks.
        return hmac.compare_digest(expected, event.signature)


class PolicyDigest:
    """
    Binds events to the governing policy version.
    A policy digest is a hash of the canonical policy definition;
    changing any field in the policy produces a new digest.
    """

    @staticmethod
    def compute(policy: Any) -> str:
        return _sha256(_canonical_bytes(policy))


class ProvenanceGraph:
    """
    Causal Provenance Graph.
    - Append-only in reference implementation (events are never mutated).
    - Each event declares its causal parents by event_id.
    - Integrity is verifiable: signature + payload_digest + parent links.
    - `explain(event_id)` reconstructs the causal chain back to the root.
    """

    def __init__(self, signer: EventSigner, policy_digest: str):
        self.signer = signer
        self.policy_digest = policy_digest
        self._events: Dict[str, ProvenanceEvent] = {}
        self._children: Dict[str, List[str]] = {}  # parent_id -> [child_id]

    # ---- construction ---------------------------------------------------

    def new_event(
        self,
        event_type: str,
        actor: str,
        payload: Any,
        parents: Sequence[str] = (),
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> ProvenanceEvent:
        payload_digest = _sha256(_canonical_bytes(payload))
        event = ProvenanceEvent(
            event_id=uuid.uuid4().hex,
            event_type=event_type,
            parents=tuple(parents),
            actor=actor,
            payload_digest=payload_digest,
            policy_digest=self.policy_digest,
            timestamp=time.time() if timestamp is None else timestamp,
            metadata=dict(metadata or {}),
        )
        signed = ProvenanceEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            parents=event.parents,
            actor=event.actor,
            payload_digest=event.payload_digest,
            policy_digest=event.policy_digest,
            timestamp=event.timestamp,
            metadata=event.metadata,
            signature=self.signer.sign(event),
        )
        return signed

    def append(self, event: ProvenanceEvent) -> None:
        if event.event_id in self._events:
            raise ValueError(f"Event {event.event_id} already in graph")
        for parent_id in event.parents:
            if parent_id not in self._events:
                raise ValueError(
                    f"Parent {parent_id} not in graph for event {event.event_id}"
                )
        self._events[event.event_id] = event
        self._children.setdefault(event.event_id, [])
        for parent_id in event.parents:
            self._children.setdefault(parent_id, []).append(event.event_id)

    # ---- integrity ------------------------------------------------------

    def verify_event(self, event: ProvenanceEvent) -> bool:
        """Signature and policy binding are intact."""
        if not self.signer.verify(event):
            return False
        if event.policy_digest != self.policy_digest:
            return False
        return True

    def verify_all(self) -> List[str]:
        """Return event_ids whose signature or policy binding is broken."""
        broken: List[str] = []
        for event_id, event in self._events.items():
            if not self.verify_event(event):
                broken.append(event_id)
        return broken

    def has_tamper(self) -> bool:
        return len(self.verify_all()) > 0

    # ---- causal queries -------------------------------------------------

    def get(self, event_id: str) -> Optional[ProvenanceEvent]:
        return self._events.get(event_id)

    def ancestors(self, event_id: str) -> List[ProvenanceEvent]:
        """BFS traversal of causal parents (deduped)."""
        if event_id not in self._events:
            return []
        visited: Dict[str, ProvenanceEvent] = {}
        stack: List[str] = list(self._events[event_id].parents)
        while stack:
            pid = stack.pop()
            if pid in visited or pid not in self._events:
                continue
            ev = self._events[pid]
            visited[pid] = ev
            stack.extend(ev.parents)
        # Return in chronological order.
        return sorted(visited.values(), key=lambda e: e.timestamp)

    def explain(self, event_id: str) -> List[ProvenanceEvent]:
        """
        Causal explanation: the event plus all its ancestors, ordered
        chronologically. The first element is the root intent (or the
        earliest reachable node).
        """
        if event_id not in self._events:
            return []
        chain = self.ancestors(event_id) + [self._events[event_id]]
        return sorted(chain, key=lambda e: e.timestamp)

    def find_root(self, event_id: str) -> Optional[ProvenanceEvent]:
        chain = self.explain(event_id)
        if not chain:
            return None
        return chain[0]

    def size(self) -> int:
        return len(self._events)