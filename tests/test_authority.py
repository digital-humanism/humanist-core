"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    Tests for HACP Phase 1 invariants 1, 3, 4.
"""
import time

from humanist_core.authority import (
    AgencyDecision,
    AgencyKernel,
    ProposedAction,
)


def make_envelope(**overrides):
    defaults = dict(
        actor_id="user:test",
        objective="analyse_incidents",
        operations=("read", "classify", "summarize"),
        forbidden=("delete", "send_external"),
        systems=("ServiceDesk",),
        constraints={"max_quantity": 10000},
    )
    defaults.update(overrides)
    kernel = AgencyKernel()
    return kernel, kernel.authorize_intent(**defaults)


class TestInvariant1NoSilentScopeExpansion:
    def test_in_scope_action_allowed(self):
        kernel, envelope = make_envelope()
        action = ProposedAction(operation="read", resource="dataset:incidents",
                                system="ServiceDesk")
        assert kernel.evaluate(envelope, action) == AgencyDecision.ALLOW

    def test_out_of_scope_operation_requires_reauthorization(self):
        kernel, envelope = make_envelope()
        action = ProposedAction(operation="publish", resource="report",
                                system="email", audience="management",
                                effect="reputational")
        assert kernel.evaluate(envelope, action) == AgencyDecision.REAUTHORIZE

    def test_forbidden_operation_denied(self):
        kernel, envelope = make_envelope()
        action = ProposedAction(operation="delete", resource="dataset:records")
        assert kernel.evaluate(envelope, action) == AgencyDecision.DENY

    def test_system_boundary_enforced(self):
        kernel, envelope = make_envelope()
        action = ProposedAction(operation="read", resource="x", system="HR")
        assert kernel.evaluate(envelope, action) == AgencyDecision.REAUTHORIZE

    def test_expired_envelope_requires_reauthorization(self):
        kernel, envelope = make_envelope(ttl=-1)
        action = ProposedAction(operation="read", resource="x",
                                system="ServiceDesk")
        assert kernel.evaluate(envelope, action) == AgencyDecision.REAUTHORIZE


class TestInvariant3ApprovalIsBounded:
    def test_token_covers_only_permitted_operation(self):
        kernel, envelope = make_envelope()
        kernel.issue_decision_token(envelope, permits="delete",
                                    resource="dataset:expired",
                                    max_quantity=18432)
        permitted = ProposedAction(operation="delete",
                                   resource="dataset:expired", quantity=18432)
        assert kernel.evaluate(envelope, permitted) == AgencyDecision.ALLOW_WITH_AUDIT

        other_op = ProposedAction(operation="send_external",
                                  resource="dataset:expired")
        assert kernel.evaluate(envelope, other_op) == AgencyDecision.DENY

    def test_token_quantity_bound(self):
        kernel, envelope = make_envelope()
        kernel.issue_decision_token(envelope, permits="delete",
                                    resource="dataset:expired", max_quantity=100)
        over = ProposedAction(operation="delete", resource="dataset:expired",
                              quantity=500)
        assert kernel.evaluate(envelope, over) == AgencyDecision.DENY

    def test_token_resource_bound(self):
        kernel, envelope = make_envelope()
        kernel.issue_decision_token(envelope, permits="delete",
                                    resource="dataset:expired")
        other = ProposedAction(operation="delete", resource="dataset:production")
        assert kernel.evaluate(envelope, other) == AgencyDecision.DENY


class TestInvariant4ApprovalExpires:
    def test_token_expires(self):
        kernel, envelope = make_envelope()
        now = time.time()
        kernel.issue_decision_token(envelope, permits="delete",
                                    resource="dataset:expired", expires_in=300)
        action = ProposedAction(operation="delete", resource="dataset:expired")
        assert kernel.evaluate(envelope, action, now=now) == AgencyDecision.ALLOW_WITH_AUDIT
        assert kernel.evaluate(envelope, action, now=now + 301) == AgencyDecision.REAUTHORIZE


class TestSemanticBoundaries:
    def test_constraint_exceeded_requires_checkpoint(self):
        kernel, envelope = make_envelope()
        action = ProposedAction(operation="read", resource="x",
                                system="ServiceDesk", quantity=20000)
        assert kernel.evaluate(envelope, action) == AgencyDecision.CHECKPOINT

    def test_externality_requires_checkpoint(self):
        kernel, envelope = make_envelope(operations=("read", "summarize", "publish"))
        action = ProposedAction(operation="publish", resource="report",
                                audience="management", effect="reputational")
        assert kernel.evaluate(envelope, action) == AgencyDecision.CHECKPOINT

    def test_modify_within_scope_is_audited(self):
        kernel, envelope = make_envelope(operations=("read", "modify"))
        action = ProposedAction(operation="modify", resource="record:1",
                                system="ServiceDesk")
        assert kernel.evaluate(envelope, action) == AgencyDecision.ALLOW_WITH_AUDIT