"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Auxiliary: Autonomous Loop Breaking.
    Tests for the AgencyGuardCallback LangChain adapter.
    See ARCHITECTURE.md (Agency Guard) and docs/ARCHITECTURE_v2.0.md.
"""
import pytest

from humanist_core.loop_breaker import AutonomousLoopDetected, MasqueradeDetected
from humanist_core.integrations.langchain_guard import AgencyGuardCallback


class StubVectorAnalyzer:
    """Deterministic stand-in for the semantic vector analyzer."""

    def __init__(self, similarity=0.1, threshold=0.9):
        self.similarity = similarity
        self.similarity_threshold = threshold
        self.checked = []

    def check_similarity(self, text):
        self.checked.append(text)
        return self.similarity


class StubGuard:
    """Minimal guard implementing the interface used by the callback."""

    def __init__(self, similarity=0.1, threshold=0.9, intercept_error=None):
        self.vector_analyzer = StubVectorAnalyzer(similarity, threshold)
        self.intercept_error = intercept_error
        self.intercepts = []

    def intercept_human_input(self, session_id, input_text, response_text, elapsed_time_sec):
        self.intercepts.append((session_id, input_text, response_text, elapsed_time_sec))
        if self.intercept_error is not None:
            raise self.intercept_error


class StubLedger:
    """SafeHarborLedger stand-in (not exercised by the callback yet)."""


class StubGeneration:
    def __init__(self, text):
        self.text = text


class StubResponse:
    def __init__(self, text):
        self.generations = [[StubGeneration(text)]]


def make_callback(guard=None, max_auto_hops=3):
    """Build a callback wired to stubs."""
    return AgencyGuardCallback(
        guard=guard or StubGuard(),
        ledger=StubLedger(),
        max_auto_hops=max_auto_hops,
    )


class TestOnChainStart:
    """Human initiation resets session state."""

    def test_resets_session_state(self):
        cb = make_callback()
        cb.on_chain_start({}, {"input": "do something"}, run_id="run-1", parent_run_id="sess-1")
        assert cb.session_hops["sess-1"] == 0
        assert "sess-1" in cb.session_start_times

    def test_falls_back_to_run_id(self):
        cb = make_callback()
        cb.on_chain_start({}, {}, run_id="run-2")
        assert cb.session_hops["run-2"] == 0


class TestOnToolEnd:
    """Autonomous hop limit enforcement."""

    def test_increments_hops(self):
        cb = make_callback(max_auto_hops=3)
        cb.on_chain_start({}, {}, run_id="r", parent_run_id="s")
        for i in range(3):
            cb.on_tool_end(f"out-{i}", run_id=f"t{i}", parent_run_id="s")
        assert cb.session_hops["s"] == 3

    def test_raises_when_hop_limit_exceeded(self):
        cb = make_callback(max_auto_hops=2)
        cb.on_chain_start({}, {}, run_id="r", parent_run_id="s")
        cb.on_tool_end("a", run_id="t1", parent_run_id="s")
        cb.on_tool_end("b", run_id="t2", parent_run_id="s")
        with pytest.raises(AutonomousLoopDetected):
            cb.on_tool_end("c", run_id="t3", parent_run_id="s")

    def test_stores_pending_tool_output(self):
        cb = make_callback()
        cb.on_tool_end("payload", run_id="t1", parent_run_id="s")
        assert cb.pending_tool_outputs["s"] == "payload"


class TestOnLlmEnd:
    """LLM output verification rules."""

    def test_vector_alert_does_not_raise(self):
        guard = StubGuard(similarity=0.97, threshold=0.9)
        cb = make_callback(guard)
        cb.on_llm_end(StubResponse("repeated structure"), run_id="r", parent_run_id="s")
        assert guard.vector_analyzer.checked == ["repeated structure"]

    def test_approval_request_triggers_intercept(self):
        guard = StubGuard()
        cb = make_callback(guard)
        cb.on_tool_end("tool payload", run_id="t", parent_run_id="s")
        cb.on_llm_end(StubResponse("PLAN: do the thing"), run_id="r", parent_run_id="s")
        assert len(guard.intercepts) == 1
        session_id, input_text, response_text, _ = guard.intercepts[0]
        assert session_id == "s"
        assert input_text == "tool payload"
        assert response_text == "PLAN: do the thing"

    def test_masquerade_converted_to_loop_detected(self):
        guard = StubGuard(intercept_error=MasqueradeDetected("fake approval"))
        cb = make_callback(guard)
        with pytest.raises(AutonomousLoopDetected):
            cb.on_llm_end(StubResponse("ACTION REQUIRED: approve"), run_id="r", parent_run_id="s")

    def test_generic_error_is_swallowed(self):
        guard = StubGuard(intercept_error=ValueError("boom"))
        cb = make_callback(guard)
        # Generic errors must not propagate out of the callback
        cb.on_llm_end(StubResponse("PLAN: x"), run_id="r", parent_run_id="s")