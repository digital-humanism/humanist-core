"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 5.1: Legacy Coverage Hardening.
    Targeted tests for uncovered branches in provenance (Phase 3),
    authority (Phase 1) and boundary (Phase 2).
    See docs/ARCHITECTURE_v2.0.md, Sections 8-12.
"""
from dataclasses import replace

import pytest

from humanist_core.authority import AgencyDecision, AgencyKernel, ProposedAction
from humanist_core.boundary import RiskEngine, SemanticAction, SemanticDeltaGuard
from humanist_core.provenance import (
    EventSigner,
    ProvenanceEvent,
    ProvenanceGraph,
)


def make_event(event_id="e1", parents=(), policy_digest="policy-A", signature=None):
    """Build a minimal valid ProvenanceEvent."""
    return ProvenanceEvent(
        event_id=event_id,
        event_type="intent",
        parents=parents,
        actor="user:test",
        payload_digest="digest",
        policy_digest=policy_digest,
        signature=signature,
    )


class TestProvenanceEvent:
    def test_parents_list_coerced_to_tuple(self):
        """Line 70: list parents are stored as tuple for hashability."""
        ev = make_event(parents=["a", "b"])
        assert ev.parents == ("a", "b")


class TestEventSigner:
    def test_empty_key_rejected(self):
        """Line 91: empty signing key raises ValueError."""
        with pytest.raises(ValueError):
            EventSigner(b"")

    def test_verify_unsigned_event_returns_false(self):
        """Line 100: verify fails fast on missing signature."""
        signer = EventSigner(b"test-key")
        ev = make_event()  # signature=None
        assert signer.verify(ev) is False


class TestProvenanceGraphIntegrity:
    def test_verify_event_detects_policy_mismatch(self):
        """Line 188: valid signature but wrong policy digest is rejected."""
        signer = EventSigner(b"test-key")
        graph = ProvenanceGraph(signer, "policy-A")
        unsigned = make_event(policy_digest="policy-B")
        # replace() preserves timestamp and all other fields, so the
        # signature stays valid and only the policy check can fail
        signed = replace(unsigned, signature=signer.sign(unsigned))
        assert graph.verify_event(signed) is False

    def test_get_returns_none_for_unknown_id(self):
        """Line 205: lookup of unknown event id."""
        signer = EventSigner(b"test-key")
        graph = ProvenanceGraph(signer, "policy-A")
        assert graph.get("missing") is None

    def test_ancestors_of_unknown_id_is_empty(self):
        """Line 210: ancestors of unknown event id."""
        signer = EventSigner(b"test-key")
        graph = ProvenanceGraph(signer, "policy-A")
        assert graph.ancestors("missing") == []

    def test_ancestors_dedupes_shared_ancestor(self):
        """Line 216: diamond causality — shared ancestor visited once."""
        signer = EventSigner(b"test-key")
        graph = ProvenanceGraph(signer, "policy-A")

        root = graph.new_event(
            event_type="intent", actor="user:test", payload={"objective": "x"}
        )
        graph.append(root)

        mid = graph.new_event(
            event_type="tool_call", actor="agent", payload={},
            parents=[root.event_id],
        )
        graph.append(mid)

        # leaf ссылается и на root, и на mid (который сам происходит от root)
        leaf = graph.new_event(
            event_type="tool_result", actor="agent", payload={},
            parents=[root.event_id, mid.event_id],
        )
        graph.append(leaf)

        ancestors = graph.ancestors(leaf.event_id)
        ancestor_ids = [e.event_id for e in ancestors]

        # Общий предок встречается ровно один раз (dedup через continue)
        assert ancestor_ids.count(root.event_id) == 1
        assert set(ancestor_ids) == {root.event_id, mid.event_id}

    def test_find_root_of_unknown_id_is_none(self):
        """Line 237: find_root on unknown event id."""
        signer = EventSigner(b"test-key")
        graph = ProvenanceGraph(signer, "policy-A")
        assert graph.find_root("missing") is None


class TestAuthorityAudienceCheckpoint:
    def test_external_audience_forces_checkpoint(self):
        """Line 132: audience beyond requester/self requires human decision."""
        kernel = AgencyKernel()
        envelope = kernel.authorize_intent(
            actor_id="user:test",
            objective="coverage hardening",
            operations=("read",),
            forbidden=(),
            systems=(),
            constraints={},
        )
        action = ProposedAction(
            operation="read",
            resource="document",
            system="",
            effect="informational",
            audience="public",
        )
        assert kernel.evaluate(envelope, action) == AgencyDecision.CHECKPOINT


class TestBoundaryBranches:
    def test_scope_change_detected(self):
        """Line 84: internal -> external scope is a boundary dimension."""
        guard = SemanticDeltaGuard()
        original = SemanticAction(verb="read", object="db", scope="internal")
        proposed = SemanticAction(verb="read", object="db", scope="external")
        delta = guard.compare(original, proposed)
        assert "scope" in delta.dimensions_changed

    def test_policy_overrides_applied(self):
        """Lines 196-198: policy overrides set known risk dimensions only."""
        engine = RiskEngine()
        risk = engine.evaluate(
            verb="read",
            policy_overrides={"externality": 9, "not_a_dimension": 5},
        )
        assert risk.externality == 9