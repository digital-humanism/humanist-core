"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    Tests for HACP Phase 3 — Cryptographic Provenance (Invariant 5).
"""
import time

from humanist_core.provenance import (
    EventSigner,
    PolicyDigest,
    ProvenanceEvent,
    ProvenanceGraph,
)


SIGNING_KEY = b"test-signing-key-please-change-in-production"


def build_graph():
    signer = EventSigner(SIGNING_KEY)
    policy = {"version": "v1.2", "max_auto_hops": 3, "boundaries": "strict"}
    policy_digest = PolicyDigest.compute(policy)
    return ProvenanceGraph(signer, policy_digest), signer, policy_digest


class TestProvenanceEventSigning:
    def test_sign_then_verify(self):
        signer = EventSigner(SIGNING_KEY)
        event = ProvenanceEvent(
            event_id="e1",
            event_type="intent",
            parents=(),
            actor="user:test",
            payload_digest="abc",
            policy_digest="p1",
        )
        signed = ProvenanceEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            parents=event.parents,
            actor=event.actor,
            payload_digest=event.payload_digest,
            policy_digest=event.policy_digest,
            timestamp=event.timestamp,
            signature=signer.sign(event),
        )
        assert signer.verify(signed)

    def test_wrong_key_rejects(self):
        signer_a = EventSigner(b"key-a")
        signer_b = EventSigner(b"key-b")
        event = ProvenanceEvent(
            event_id="e1", event_type="intent", parents=(),
            actor="u", payload_digest="x", policy_digest="p",
        )
        signed = ProvenanceEvent(
            event_id=event.event_id, event_type=event.event_type,
            parents=event.parents, actor=event.actor,
            payload_digest=event.payload_digest,
            policy_digest=event.policy_digest,
            signature=signer_a.sign(event),
        )
        assert signer_b.verify(signed) is False

    def test_unknown_event_type_rejected(self):
        import pytest
        with pytest.raises(ValueError):
            ProvenanceEvent(
                event_id="e1", event_type="bogus", parents=(),
                actor="u", payload_digest="x", policy_digest="p",
            )


class TestProvenanceGraphStructure:
    def test_append_and_size(self):
        graph, _, _ = build_graph()
        intent = graph.new_event("intent", "user:test", {"objective": "analyse"})
        graph.append(intent)
        call = graph.new_event(
            "tool_call", "agent:main", {"op": "read", "resource": "incidents"},
            parents=[intent.event_id],
        )
        graph.append(call)
        assert graph.size() == 2

    def test_orphan_parent_rejected(self):
        import pytest
        graph, _, _ = build_graph()
        event = graph.new_event(
            "tool_call", "agent:main", {"op": "read"},
            parents=["nonexistent"],
        )
        with pytest.raises(ValueError):
            graph.append(event)

    def test_duplicate_event_rejected(self):
        import pytest
        graph, _, _ = build_graph()
        event = graph.new_event("intent", "user:test", {"objective": "x"})
        graph.append(event)
        with pytest.raises(ValueError):
            graph.append(event)


class TestCausalProvenance:
    def _build_chain(self):
        graph, _, _ = build_graph()
        intent = graph.new_event("intent", "user:test", {"objective": "analyse"})
        graph.append(intent)

        read = graph.new_event(
            "tool_call", "agent:main",
            {"op": "read", "resource": "incidents"},
            parents=[intent.event_id],
        )
        graph.append(read)

        delta = graph.new_event(
            "semantic_delta", "agent:main",
            {"from": "analyse", "to": "publish"},
            parents=[read.event_id],
        )
        graph.append(delta)

        decision = graph.new_event(
            "decision", "user:test",
            {"permits": "publish", "ttl": 300},
            parents=[delta.event_id],
        )
        graph.append(decision)

        action = graph.new_event(
            "action", "agent:main",
            {"op": "publish", "resource": "report"},
            parents=[decision.event_id],
        )
        graph.append(action)
        return graph, intent, action

    def test_explain_returns_causal_chain(self):
        graph, intent, action = self._build_chain()
        chain = graph.explain(action.event_id)
        types = [e.event_type for e in chain]
        assert types == ["intent", "tool_call", "semantic_delta",
                         "decision", "action"]

    def test_find_root_returns_original_intent(self):
        graph, intent, action = self._build_chain()
        root = graph.find_root(action.event_id)
        assert root is not None
        assert root.event_id == intent.event_id
        assert root.event_type == "intent"

    def test_explain_unknown_returns_empty(self):
        graph, _, _ = build_graph()
        assert graph.explain("does-not-exist") == []


class TestTamperDetection:
    def test_tampered_signature_detected(self):
        graph, _, _ = build_graph()
        event = graph.new_event("intent", "user:test", {"objective": "x"})
        graph.append(event)
        assert graph.verify_all() == []

        # Simulate tampering: replace signature on stored event.
        tampered = ProvenanceEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            parents=event.parents,
            actor=event.actor,
            payload_digest=event.payload_digest,
            policy_digest=event.policy_digest,
            timestamp=event.timestamp,
            metadata=event.metadata,
            signature="deadbeef" * 8,
        )
        graph._events[event.event_id] = tampered  # type: ignore[attr-defined]
        assert graph.has_tamper()
        assert event.event_id in graph.verify_all()

    def test_policy_digest_mismatch_detected(self):
        graph, signer, _ = build_graph()
        event = graph.new_event("intent", "user:test", {"objective": "x"})
        graph.append(event)
        # Re-bind the same event to a different policy digest.
        rogue = ProvenanceEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            parents=event.parents,
            actor=event.actor,
            payload_digest=event.payload_digest,
            policy_digest="different-policy-digest",
            timestamp=event.timestamp,
            signature=signer.sign(event),  # signature still matches old digest
        )
        graph._events[event.event_id] = rogue  # type: ignore[attr-defined]
        assert graph.has_tamper()


class TestInvariant5ProvenanceIsCausal:
    def test_consequential_action_has_causal_explanation(self):
        """
        Invariant 5: the system can reconstruct WHY a consequential
        action was allowed, walking back to the original intent.
        """
        graph, _, _ = build_graph()

        intent = graph.new_event("intent", "user:test",
                                 {"objective": "analyse incidents"})
        graph.append(intent)

        analysis = graph.new_event(
            "tool_call", "agent:main",
            {"op": "analyse", "resource": "incidents"},
            parents=[intent.event_id],
        )
        graph.append(analysis)

        delta = graph.new_event(
            "semantic_delta", "agent:main",
            {"from": "analyse", "to": "publish",
             "audience": "management", "effect": "reputational"},
            parents=[analysis.event_id],
        )
        graph.append(delta)

        checkpoint = graph.new_event(
            "checkpoint", "system:kernel",
            {"reason": "externality boundary"},
            parents=[delta.event_id],
        )
        graph.append(checkpoint)

        human_decision = graph.new_event(
            "decision", "user:test",
            {"permits": "publish", "resource": "report",
             "max_quantity": 1, "ttl": 300},
            parents=[checkpoint.event_id],
        )
        graph.append(human_decision)

        action = graph.new_event(
            "action", "agent:main",
            {"op": "publish", "resource": "report",
             "audience": "management"},
            parents=[human_decision.event_id],
        )
        graph.append(action)

        # The system MUST be able to explain the action.
        chain = graph.explain(action.event_id)
        assert len(chain) >= 6
        assert chain[0].event_type == "intent"
        assert chain[-1].event_type == "action"
        assert any(e.event_type == "decision" for e in chain)
        assert any(e.event_type == "semantic_delta" for e in chain)
        assert not graph.has_tamper()