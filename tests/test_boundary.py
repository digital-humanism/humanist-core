"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    Tests for HACP Phase 2 invariants 2, 5, 7.
"""
import pytest

from humanist_core.boundary import (
    AutonomyBudget,
    RiskEngine,
    RiskLevel,
    SemanticAction,
    SemanticDeltaGuard,
)


class TestSemanticDeltaGuard:
    def test_no_change_detected(self):
        guard = SemanticDeltaGuard()
        original = SemanticAction(
            verb="analyse", object="incidents", effect="informational",
            audience="requester", reversibility="reversible", scope="internal"
        )
        proposed = SemanticAction(
            verb="analyse", object="incidents", effect="informational",
            audience="requester", reversibility="reversible", scope="internal"
        )
        delta = guard.compare(original, proposed)
        assert not delta.is_meaningful()

    def test_read_to_write_boundary(self):
        guard = SemanticDeltaGuard()
        original = SemanticAction(
            verb="read", object="records", effect="informational",
            audience="requester"
        )
        proposed = SemanticAction(
            verb="modify", object="records", effect="operational",
            audience="requester"
        )
        delta = guard.compare(original, proposed)
        assert delta.is_meaningful()
        assert "verb" in delta.dimensions_changed
        assert delta.boundary_type == "read_write"

    def test_internal_to_external_boundary(self):
        guard = SemanticDeltaGuard()
        original = SemanticAction(
            verb="analyse", object="data", audience="requester", scope="internal"
        )
        proposed = SemanticAction(
            verb="analyse", object="data", audience="management", scope="internal"
        )
        delta = guard.compare(original, proposed)
        assert delta.is_meaningful()
        assert "audience" in delta.dimensions_changed
        assert delta.boundary_type == "internal_external"

    def test_reversible_to_irreversible_boundary(self):
        guard = SemanticDeltaGuard()
        original = SemanticAction(
            verb="modify", object="records", reversibility="reversible"
        )
        proposed = SemanticAction(
            verb="modify", object="records", reversibility="irreversible"
        )
        delta = guard.compare(original, proposed)
        assert delta.is_meaningful()
        assert "reversibility" in delta.dimensions_changed
        assert delta.boundary_type == "reversible_irreversible"


class TestRiskEngine:
    def test_low_risk_operation(self):
        engine = RiskEngine()
        risk = engine.evaluate("read", audience="requester", scope="internal")
        assert risk.level == RiskLevel.LOW
        assert risk.autonomy_cost < 5

    def test_medium_risk_operation(self):
        engine = RiskEngine()
        risk = engine.evaluate("modify", audience="requester", scope="internal")
        assert risk.level == RiskLevel.MEDIUM

    def test_high_risk_operation(self):
        engine = RiskEngine()
        risk = engine.evaluate("delete", audience="requester", scope="internal")
        assert risk.level == RiskLevel.HIGH
        assert risk.irreversibility > 5

    def test_critical_risk_operation(self):
        engine = RiskEngine()
        risk = engine.evaluate("publish", audience="external", scope="external")
        assert risk.level == RiskLevel.CRITICAL
        assert risk.externality > 10

    def test_sensitive_data_increases_risk(self):
        engine = RiskEngine()
        risk_normal = engine.evaluate("read", data_class="public")
        risk_sensitive = engine.evaluate("read", data_class="pii")
        assert risk_sensitive.privacy > risk_normal.privacy

    def test_large_quantity_increases_blast_radius(self):
        engine = RiskEngine()
        risk_small = engine.evaluate("modify", quantity=100)
        risk_large = engine.evaluate("modify", quantity=5000)
        assert risk_large.blast_radius > risk_small.blast_radius


class TestAutonomyBudget:
    def test_budget_allows_low_risk_actions(self):
        budget = AutonomyBudget(budget_limit=50)
        engine = RiskEngine()
        
        for _ in range(10):
            risk = engine.evaluate("read")
            assert budget.consume(risk) is True
        
        assert budget.actions_count() == 10
        assert budget.remaining() > 0

    def test_budget_blocks_high_risk_actions(self):
        budget = AutonomyBudget(budget_limit=10)
        engine = RiskEngine()

        # "delete" costs 18: irreversibility 8 + externality 2
        # + privacy 2 + privilege 6 -> exceeds a budget of 10
        risk = engine.evaluate("delete")
        assert risk.level == RiskLevel.HIGH
        assert budget.consume(risk) is False
        assert budget.consumed == 0

    def test_budget_exhaustion(self):
        budget = AutonomyBudget(budget_limit=30)
        engine = RiskEngine()
        
        # Consume budget with medium-risk actions
        for _ in range(5):
            risk = engine.evaluate("modify")
            budget.consume(risk)
        
        # Next action should fail
        risk = engine.evaluate("modify")
        assert budget.consume(risk) is False

    def test_budget_reset(self):
        budget = AutonomyBudget(budget_limit=50)
        engine = RiskEngine()
        
        risk = engine.evaluate("modify")
        budget.consume(risk)
        assert budget.consumed > 0
        
        budget.reset()
        assert budget.consumed == 0
        assert budget.actions_count() == 0


class TestInvariant2HighImpactRequiresAuthority:
    def test_critical_action_requires_checkpoint(self):
        """Invariant 2: High-impact actions require explicit authority."""
        budget = AutonomyBudget(budget_limit=10)
        engine = RiskEngine()
        
        # Critical risk action exceeds small budget
        risk = engine.evaluate("delete", audience="external", scope="external")
        assert risk.level == RiskLevel.CRITICAL
        assert budget.can_act(risk) is False


class TestInvariant5ProvenanceIsCausal:
    def test_actions_tracked(self):
        """Invariant 5: Provenance is causal — actions are tracked."""
        budget = AutonomyBudget(budget_limit=100)
        engine = RiskEngine()
        
        risk1 = engine.evaluate("read")
        risk2 = engine.evaluate("analyse")
        risk3 = engine.evaluate("summarize")
        
        budget.consume(risk1)
        budget.consume(risk2)
        budget.consume(risk3)
        
        assert budget.actions_count() == 3
        assert budget.consumed > 0


class TestInvariant7SemanticChangeIsSecurityRelevant:
    def test_semantic_boundary_detected(self):
        """Invariant 7: Semantic change is security-relevant."""
        guard = SemanticDeltaGuard()
        
        original = SemanticAction(
            verb="analyse", object="incidents", effect="informational",
            audience="requester"
        )
        proposed = SemanticAction(
            verb="send", object="findings", effect="reputational",
            audience="management"
        )
        
        delta = guard.compare(original, proposed)
        assert delta.is_meaningful()
        assert len(delta.dimensions_changed) > 0