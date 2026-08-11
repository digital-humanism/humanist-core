"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 4: LangChain Integration.
    Hardening tests for uncovered branches in HumanistCallback.
    See docs/ARCHITECTURE_v2.0.md, Sections 13-15.
"""
import pytest

from langchain_core.agents import AgentFinish

from humanist_core.authority import AgencyDecision
from humanist_core.integrations.langchain_v2 import (
    AutonomousLoopDetected,
    HumanistCallback,
    ReauthorizationRequired,
    SemanticBoundaryDetected,
)


def make_callback(**overrides):
    """Build a HumanistCallback with sensible test defaults."""
    kwargs = dict(
        actor_id="user:test",
        objective="test objective",
        operations=("read", "analyse", "modify", "delete"),
        forbidden=(),
        autonomy_budget=1000.0,
    )
    kwargs.update(overrides)
    return HumanistCallback(**kwargs)


def tool_call(cb, name, run_id="t1"):
    """Simulate a LangChain tool start event."""
    cb.on_tool_start({"name": name}, "input", run_id=run_id)


class TestChainLifecycle:
    """Session lifecycle and accessor branches."""

    def test_on_chain_start_sets_session(self):
        cb = make_callback()
        cb.on_chain_start({}, {}, run_id="sess-1")
        assert cb._session_id == "sess-1"

    def test_on_agent_finish_records_event(self):
        cb = make_callback()
        cb.on_chain_start({}, {}, run_id="sess-1")
        finish = AgentFinish(return_values={"output": "done"}, log="")
        cb.on_agent_finish(finish, run_id="f1")

    def test_getters(self):
        cb = make_callback()
        assert cb.get_provenance_graph() is cb.provenance
        status = cb.get_autonomy_budget_status()
        assert {"consumed", "limit", "remaining"} == set(status.keys())


class TestAutonomyBudgetExhaustion:
    """Budget exhaustion raises AutonomousLoopDetected."""

    def test_zero_budget_raises_on_first_tool(self):
        cb = make_callback(autonomy_budget=0.0)
        with pytest.raises(AutonomousLoopDetected):
            tool_call(cb, "delete_records")


class TestIntentEnvelopeEnforcement:
    """DENY and REAUTHORIZE decisions raise ReauthorizationRequired."""

    def test_forbidden_operation_raises(self):
        cb = make_callback(operations=("read",), forbidden=("delete",))
        with pytest.raises(ReauthorizationRequired) as exc_info:
            tool_call(cb, "delete_records")
        assert "forbidden" in exc_info.value.reason.lower()

    def test_unlisted_operation_raises(self):
        cb = make_callback(operations=("read",), forbidden=())
        with pytest.raises(ReauthorizationRequired) as exc_info:
            tool_call(cb, "publish_report")
        assert "exceeds" in exc_info.value.reason.lower()


class TestSemanticBoundary:
    """Meaningful semantic delta raises SemanticBoundaryDetected."""

    def test_read_then_delete_crosses_boundary(self):
        cb = make_callback(operations=("read", "delete"))
        tool_call(cb, "read_document")
        with pytest.raises(SemanticBoundaryDetected) as exc_info:
            tool_call(cb, "delete_document")
        assert exc_info.value.boundary_type


class TestCheckpointDecision:
    """CHECKPOINT decision records event and raises."""

    def test_checkpoint_raises_semantic_boundary(self):
        cb = make_callback()
        # Force the kernel decision deterministically
        cb.kernel.evaluate = lambda envelope, proposed: AgencyDecision.CHECKPOINT
        with pytest.raises(SemanticBoundaryDetected) as exc_info:
            tool_call(cb, "read_document")
        assert exc_info.value.boundary_type == "checkpoint_required"

class TestAgentActionNoop:
    """on_agent_action is intentionally a no-op (handled in on_tool_start)."""

    def test_on_agent_action_is_noop(self):
        from langchain_core.agents import AgentAction
        cb = make_callback()
        action = AgentAction(tool="search", tool_input="query", log="")
        cb.on_agent_action(action, run_id="a1")

class TestHeuristicBranches:
    """Remaining branches in _extract_operation / _infer_effect."""

    def test_modify_extraction_and_operational_effect(self):
        cb = make_callback()
        tool_call(cb, "update_document")
        assert cb._last_action_semantic.verb == "modify"
        assert cb._last_action_semantic.effect == "operational"

    def test_default_extraction_analyse(self):
        cb = make_callback()
        # Avoid names containing keyword substrings ("widget" contains "get")
        tool_call(cb, "compute_totals")
        assert cb._last_action_semantic.verb == "analyse"
        assert cb._last_action_semantic.effect == "informational"

    def test_unknown_effect_fallback(self):
        cb = make_callback()
        assert cb._infer_effect("teleport") == "unknown"