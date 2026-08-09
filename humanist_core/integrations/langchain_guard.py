"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3
"""
import time
from typing import Dict, Any, List, Optional
try:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.outputs import LLMResult
except ImportError:
    BaseCallbackHandler = object
    LLMResult = None

from humanist_core.loop_breaker import AgencyGuardV2, AutonomousLoopDetected, MasqueradeDetected
from humanist_core.safe_harbor import SafeHarborLedger

class AgencyGuardCallback(BaseCallbackHandler):
    """
    Immune system for LangChain.
    Intercepts agent execution loops and applies Humanist principles.
    """
    def __init__(self, guard: AgencyGuardV2, ledger: SafeHarborLedger, max_auto_hops: int = 3):
        self.guard = guard
        self.ledger = ledger
        self.max_auto_hops = max_auto_hops
        
        # Session state tracking (using parent_run_id to track the whole chain)
        self.session_hops = {}
        self.session_start_times = {}
        self.pending_tool_outputs = {}

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: str, parent_run_id: Optional[str] = None, **kwargs):
        session_id = parent_run_id or run_id
        
        # Reset autonomous counters on human initiation
        self.session_hops[session_id] = 0
        self.session_start_times[session_id] = time.time()
        
        human_input = inputs.get("input", "")
        
        # In production, this should call SafeHarbor to sign the intent
        # record_id = self.ledger.log_intent("AGENTIC_TASK", human_input, stance="Approved by User")
        print(f"[GUARD] Human intent registered. Session: {session_id}")

    def on_tool_end(self, output: str, *, run_id: str, parent_run_id: Optional[str] = None, **kwargs):
        session_id = parent_run_id or run_id
        
        # Increment machine hop counter
        self.session_hops[session_id] = self.session_hops.get(session_id, 0) + 1
        self.pending_tool_outputs[session_id] = output
        
        # Rule 1: Autonomous hop limit
        if self.session_hops[session_id] > self.max_auto_hops:
            raise AutonomousLoopDetected(
                f"Agent exceeded {self.max_auto_hops} autonomous hops. "
                "Semantic Checkpoint and human confirmation required."
            )

    def on_llm_end(self, response: Any, *, run_id: str, parent_run_id: Optional[str] = None, **kwargs):
        if LLMResult is None: return
        
        session_id = parent_run_id or run_id
        try:
            generated_text = response.generations[0][0].text
            
            # Rule 2: Check vector entropy
            similarity_score = self.guard.vector_analyzer.check_similarity(generated_text)
            if similarity_score >= self.guard.vector_analyzer.similarity_threshold:
                print(f"[VECTOR ALERT] Structural anomaly detected ({similarity_score*100}% match).")

            # Rule 3: Cognitive load verification (if agent asks for approval)
            if "PLAN:" in generated_text or "ACTION REQUIRED:" in generated_text:
                tool_output = self.pending_tool_outputs.get(session_id, "")
                elapsed_time = time.time() - self.session_start_times.get(session_id, time.time())
                
                self.guard.intercept_human_input(
                    session_id=session_id,
                    input_text=tool_output,
                    response_text=generated_text,
                    elapsed_time_sec=elapsed_time
                )
        except MasqueradeDetected as e:
            print(f"[GUARD] Blocked: {e}")
            raise AutonomousLoopDetected("Attempt to simulate human approval detected.") from e
        except Exception as e:
            print(f"[GUARD ERROR] {e}")