"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    Tests for LangChain integration.
"""
import pytest

from humanist_core.integrations.langchain_v2 import (
    AutonomousLoopDetected,
    HumanistCallback,
    ReauthorizationRequired,
    SemanticBoundaryDetected,
)


class TestLangChainIntegration:
    def test_callback_initializes_with_intent(self):
        callback = HumanistCallback(
            actor_id="user:test",
            objective="analyse incidents",
            operations=["read", "analyse"],
        )
        assert callback.envelope.objective == "analyse incidents"
        assert callback.provenance.size() == 1  # Intent event recorded

    def test_tool_start_records_provenance(self):
        callback = HumanistCallback(
            actor_id="user:test",
            objective="analyse",
            operations=["read"],
        )
        
        # Simulate tool call
        callback.on_tool_start(
            serialized={"name": "search_tool"},
            input_str="query",
            run_id="run-123",
        )
        
        assert callback.provenance.size() == 2  # Intent + tool_call

    def test_autonomy_budget_exhaustion(self):
        callback = HumanistCallback(
            actor_id="user:test",
            objective="analyse",
            operations=["read"],
            autonomy_budget=5.0,  # Very low budget
        )
        
        # First few reads should pass
        for i in range(3):
            callback.on_tool_start(
                serialized={"name": "search_tool"},
                input_str=f"query-{i}",
                run_id=f"run-{i}",
            )
        
        # Budget should be getting close to limit
        status = callback.get_autonomy_budget_status()
        assert status["consumed"] > 0
        
        # Eventually should exhaust budget
        with pytest.raises(AutonomousLoopDetected):
            for i in range(10):
                callback.on_tool_start(
                    serialized={"name": "search_tool"},
                    input_str=f"query-{i}",
                    run_id=f"run-{i}",
                )

    def test_forbidden_operation_denied(self):
        callback = HumanistCallback(
            actor_id="user:test",
            objective="analyse",
            operations=["read"],
            forbidden=["delete"],
        )
        
        with pytest.raises(ReauthorizationRequired):
            callback.on_tool_start(
                serialized={"name": "delete_records"},
                input_str="delete all",
                run_id="run-1",
            )

    def test_out_of_scope_operation_requires_reauthorization(self):
        callback = HumanistCallback(
            actor_id="user:test",
            objective="analyse",
            operations=["read", "analyse"],
        )
        
        with pytest.raises(ReauthorizationRequired):
            callback.on_tool_start(
                serialized={"name": "send_email"},
                input_str="send report",
                run_id="run-1",
            )

    def test_provenance_graph_explain(self):
        callback = HumanistCallback(
            actor_id="user:test",
            objective="analyse",
            operations=["read"],
        )
        
        callback.on_tool_start(
            serialized={"name": "search_tool"},
            input_str="query",
            run_id="run-1",
        )
        
        # Get provenance graph
        graph = callback.get_provenance_graph()
        assert graph.size() >= 2
        
        # Should be able to explain events
        events = list(graph._events.values())
        if events:
            last_event = events[-1]
            chain = graph.explain(last_event.event_id)
            assert len(chain) >= 1

    def test_budget_status_tracking(self):
        callback = HumanistCallback(
            actor_id="user:test",
            objective="analyse",
            operations=["read"],
            autonomy_budget=100.0,
        )
        
        status = callback.get_autonomy_budget_status()
        assert status["consumed"] == 0
        assert status["limit"] == 100.0
        assert status["remaining"] == 100.0
        
        # Make a tool call
        callback.on_tool_start(
            serialized={"name": "search_tool"},
            input_str="query",
            run_id="run-1",
        )
        
        status_after = callback.get_autonomy_budget_status()
        assert status_after["consumed"] > 0
        assert status_after["remaining"] < 100.0