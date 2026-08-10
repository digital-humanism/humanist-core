"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 4: LangChain Integration.
    Runtime adapter that connects AgencyKernel + Boundary Detection +
    Provenance Graph to LangChain agent workflows.

    Usage:
        from humanist_core.integrations.langchain_v2 import HumanistCallback

        callback = HumanistCallback(
            actor_id="user:alice",
            objective="analyse incidents",
            operations=("read", "analyse", "summarize"),
            forbidden=("delete", "send_external"),
        )

        agent = create_react_agent(
            llm,
            tools,
            callbacks=[callback],
        )
"""
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.outputs import LLMResult

from humanist_core.authority import (
    AgencyDecision,
    AgencyKernel,
    IntentEnvelope,
    ProposedAction,
)
from humanist_core.boundary import (
    AutonomyBudget,
    RiskEngine,
    SemanticAction,
    SemanticDeltaGuard,
)
from humanist_core.provenance import (
    EventSigner,
    PolicyDigest,
    ProvenanceGraph,
)


class AutonomousLoopDetected(Exception):
    """Raised when agent exceeds autonomy budget without human checkpoint."""
    pass


class SemanticBoundaryDetected(Exception):
    """Raised when meaningful semantic boundary is crossed."""
    def __init__(self, boundary_type: str, message: str):
        self.boundary_type = boundary_type
        super().__init__(message)


class ReauthorizationRequired(Exception):
    """Raised when action exceeds Intent Envelope scope."""
    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Reauthorization required: {reason}")


class HumanistCallback(BaseCallbackHandler):
    """
    LangChain callback that enforces HACP v2.0 protocol:
    - Registers human intent at workflow start
    - Evaluates each tool call through AgencyKernel
    - Tracks autonomy budget consumption
    - Detects semantic boundaries
    - Records provenance graph
    - Raises exceptions to enforce checkpoints
    """

    def __init__(
        self,
        actor_id: str,
        objective: str,
        operations: Sequence[str],
        forbidden: Sequence[str] = (),
        systems: Sequence[str] = (),
        constraints: Optional[Dict[str, Any]] = None,
        autonomy_budget: float = 50.0,
        signing_key: bytes = b"default-key-change-in-production",
        policy: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        
        # Core components
        self.kernel = AgencyKernel()
        self.risk_engine = RiskEngine()
        self.delta_guard = SemanticDeltaGuard()
        self.budget = AutonomyBudget(budget_limit=autonomy_budget)
        
        # Provenance
        policy_obj = policy or {"version": "v1.0", "autonomy_budget": autonomy_budget}
        policy_digest = PolicyDigest.compute(policy_obj)
        self.signer = EventSigner(signing_key)
        self.provenance = ProvenanceGraph(self.signer, policy_digest)
        
        # Intent envelope
        self.envelope = self.kernel.authorize_intent(
            actor_id=actor_id,
            objective=objective,
            operations=operations,
            forbidden=forbidden,
            systems=systems,
            constraints=constraints or {},
        )
        
        # Session state
        self._session_id: Optional[str] = None
        self._last_intent_event_id: Optional[str] = None
        self._last_action_semantic: Optional[SemanticAction] = None
        self._last_tool_event_id: Optional[str] = None
        
        # Register intent in provenance
        intent_event = self.provenance.new_event(
            event_type="intent",
            actor=actor_id,
            payload={
                "objective": objective,
                "operations": list(operations),
                "forbidden": list(forbidden),
            },
        )
        self.provenance.append(intent_event)
        self._last_intent_event_id = intent_event.event_id

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when agent workflow starts."""
        self._session_id = str(run_id)

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called before each tool execution — enforce HACP protocol."""
        tool_name = serialized.get("name", "unknown")
        
        # Extract operation from tool name (simplified heuristic)
        operation = self._extract_operation(tool_name)
        
        # Build proposed action
        proposed = ProposedAction(
            operation=operation,
            resource=tool_name,
            system="",  # Can be enriched from metadata
        )
        
        # Evaluate through AgencyKernel
        decision = self.kernel.evaluate(self.envelope, proposed)
        
        # Record tool call in provenance
        tool_event = self.provenance.new_event(
            event_type="tool_call",
            actor="agent",
            payload={
                "tool": tool_name,
                "operation": operation,
                "input_preview": input_str[:200] if input_str else "",
            },
            parents=[self._last_intent_event_id] if self._last_intent_event_id else [],
        )
        self.provenance.append(tool_event)
        self._last_tool_event_id = tool_event.event_id
        
        # Evaluate risk and consume budget
        risk = self.risk_engine.evaluate(
            verb=operation,
            audience="",
            scope="internal",
        )
        
        if not self.budget.consume(risk):
            # Budget exhausted — require checkpoint
            checkpoint_event = self.provenance.new_event(
                event_type="checkpoint",
                actor="system",
                payload={
                    "reason": "autonomy_budget_exhausted",
                    "consumed": self.budget.consumed,
                    "limit": self.budget.budget_limit,
                },
                parents=[tool_event.event_id],
            )
            self.provenance.append(checkpoint_event)
            
            raise AutonomousLoopDetected(
                f"Autonomy budget exhausted ({self.budget.consumed:.1f}/{self.budget.budget_limit}). "
                f"Human checkpoint required before continuing."
            )
        
        # Check for semantic boundary
        current_semantic = SemanticAction(
            verb=operation,
            object=tool_name,
            effect=self._infer_effect(operation),
            audience="requester",
        )
        
        if self._last_action_semantic:
            delta = self.delta_guard.compare(self._last_action_semantic, current_semantic)
            if delta.is_meaningful():
                # Semantic boundary detected
                delta_event = self.provenance.new_event(
                    event_type="semantic_delta",
                    actor="system",
                    payload={
                        "boundary_type": delta.boundary_type,
                        "dimensions_changed": delta.dimensions_changed,
                        "from": {
                            "verb": delta.from_action.verb,
                            "object": delta.from_action.object,
                        },
                        "to": {
                            "verb": delta.to_action.verb,
                            "object": delta.to_action.object,
                        },
                    },
                    parents=[tool_event.event_id],
                )
                self.provenance.append(delta_event)
                
                raise SemanticBoundaryDetected(
                    boundary_type=delta.boundary_type,
                    message=f"Semantic boundary detected: {delta.boundary_type}. "
                            f"Changed dimensions: {delta.dimensions_changed}. "
                            f"Human checkpoint required.",
                )
        
        self._last_action_semantic = current_semantic
        
        # Handle decision
        if decision == AgencyDecision.DENY:
            raise ReauthorizationRequired(
                operation=operation,
                reason=f"Operation '{operation}' is forbidden by Intent Envelope",
            )
        elif decision == AgencyDecision.REAUTHORIZE:
            raise ReauthorizationRequired(
                operation=operation,
                reason=f"Operation '{operation}' exceeds granted scope",
            )
        elif decision == AgencyDecision.CHECKPOINT:
            checkpoint_event = self.provenance.new_event(
                event_type="checkpoint",
                actor="system",
                payload={
                    "reason": "semantic_boundary",
                    "operation": operation,
                },
                parents=[tool_event.event_id],
            )
            self.provenance.append(checkpoint_event)
            
            raise SemanticBoundaryDetected(
                boundary_type="checkpoint_required",
                message=f"Checkpoint required for operation '{operation}'",
            )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Called after tool execution — record causally linked result."""
        parents = [self._last_tool_event_id] if self._last_tool_event_id else []
        result_event = self.provenance.new_event(
            event_type="tool_result",
            actor="agent",
            payload={"output_preview": (output or "")[:200]},
            parents=parents,
        )
        self.provenance.append(result_event)
        
        # Note: In production, link to the corresponding tool_call event
        # For simplicity, we append without strict parent validation here

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Called when agent decides to take an action."""
        pass  # Handled in on_tool_start

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Called when agent workflow completes."""
        finish_event = self.provenance.new_event(
            event_type="action",
            actor="agent",
            payload={
                "output": finish.return_values.get("output", "")[:500],
            },
            parents=[self._last_intent_event_id] if self._last_intent_event_id else [],
        )
        self.provenance.append(finish_event)

    def get_provenance_graph(self) -> ProvenanceGraph:
        """Return the provenance graph for audit."""
        return self.provenance

    def get_autonomy_budget_status(self) -> Dict[str, float]:
        """Return current budget consumption."""
        return {
            "consumed": self.budget.consumed,
            "limit": self.budget.budget_limit,
            "remaining": self.budget.remaining(),
        }

    def _extract_operation(self, tool_name: str) -> str:
        """Extract operation type from tool name (simplified heuristic)."""
        tool_lower = tool_name.lower()
        if any(word in tool_lower for word in ["read", "get", "fetch", "search"]):
            return "read"
        elif any(word in tool_lower for word in ["write", "modify", "update", "edit"]):
            return "modify"
        elif any(word in tool_lower for word in ["delete", "remove"]):
            return "delete"
        elif any(word in tool_lower for word in ["send", "email", "notify"]):
            return "send"
        elif any(word in tool_lower for word in ["publish", "post"]):
            return "publish"
        else:
            return "analyse"  # Default

    def _infer_effect(self, operation: str) -> str:
        """Infer effect type from operation."""
        if operation in ("read", "analyse", "summarize"):
            return "informational"
        elif operation in ("modify", "write"):
            return "operational"
        elif operation in ("delete",):
            return "destructive"
        elif operation in ("send", "publish"):
            return "reputational"
        else:
            return "unknown"