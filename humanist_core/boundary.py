"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 2: Boundary Detection.
    Risk-weighted autonomy and semantic change detection.
    See docs/ARCHITECTURE_v2.0.md, Sections 7-9.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class SemanticAction:
    """Structured representation for semantic comparison."""
    verb: str
    object: str
    effect: str = ""
    audience: str = ""
    reversibility: str = "reversible"
    scope: str = "internal"


@dataclass(frozen=True)
class SemanticDelta:
    """Detected meaningful boundary crossing."""
    dimensions_changed: List[str]
    from_action: SemanticAction
    to_action: SemanticAction
    boundary_type: str  # "read_write", "internal_external", "reversible_irreversible"

    def is_meaningful(self) -> bool:
        return len(self.dimensions_changed) > 0


class SemanticDeltaGuard:
    """
    Detects when semantic meaning has materially changed, even if
    technical operation names remain similar.
    """
    
    BOUNDARY_DIMENSIONS = {
        "read_write": {"verb": ["read", "analyse", "summarize"]},
        "internal_external": {"audience": ["requester", "self"], "scope": ["internal"]},
        "reversible_irreversible": {"reversibility": ["reversible"]},
    }

    def compare(self, original: SemanticAction, proposed: SemanticAction) -> SemanticDelta:
        changes = []
        
        # Operation boundary
        if original.verb != proposed.verb:
            orig_category = self._get_category(original.verb, "verb")
            prop_category = self._get_category(proposed.verb, "verb")
            if orig_category != prop_category:
                changes.append("verb")
        
        # Audience boundary
        if original.audience != proposed.audience:
            orig_category = self._get_category(original.audience, "audience")
            prop_category = self._get_category(proposed.audience, "audience")
            if orig_category != prop_category:
                changes.append("audience")
        
        # Effect boundary
        if original.effect != proposed.effect and proposed.effect:
            changes.append("effect")
        
        # Reversibility boundary
        if original.reversibility != proposed.reversibility:
            changes.append("reversibility")
        
        # Scope boundary
        if original.scope != proposed.scope:
            changes.append("scope")
        
        boundary_type = self._classify_boundary(changes)
        
        return SemanticDelta(
            dimensions_changed=changes,
            from_action=original,
            to_action=proposed,
            boundary_type=boundary_type,
        )

    def _get_category(self, value: str, dimension: str) -> str:
        for boundary_name, constraints in self.BOUNDARY_DIMENSIONS.items():
            if dimension in constraints and value in constraints[dimension]:
                return boundary_name
        return "other"

    def _classify_boundary(self, changes: List[str]) -> str:
        if "verb" in changes:
            return "read_write"
        if "audience" in changes or "scope" in changes:
            return "internal_external"
        if "reversibility" in changes:
            return "reversible_irreversible"
        return "other"


@dataclass
class ActionRisk:
    """Risk assessment for a proposed action."""
    level: RiskLevel
    irreversibility: float = 0.0
    externality: float = 0.0
    financial: float = 0.0
    privacy: float = 0.0
    privilege: float = 0.0
    legal: float = 0.0
    uncertainty: float = 0.0
    blast_radius: float = 0.0

    @property
    def autonomy_cost(self) -> float:
        """Aggregate risk score for autonomy budget consumption."""
        return (
            self.irreversibility
            + self.externality
            + self.financial
            + self.privacy
            + self.privilege
            + self.legal
            + self.uncertainty
            + self.blast_radius
        )


class RiskEngine:
    """
    Evaluates consequence and risk of proposed actions.
    Risk is contextual and policy-defined.
    """
    
    # Default risk profiles (can be overridden by policy)
    OPERATION_RISK = {
        "read": {"irreversibility": 0, "externality": 0, "privacy": 0, "privilege": 1},
        "analyse": {"irreversibility": 0, "externality": 0, "privacy": 0, "privilege": 1},
        "summarize": {"irreversibility": 0, "externality": 0, "privacy": 0, "privilege": 1},
        "classify": {"irreversibility": 0, "externality": 0, "privacy": 0, "privilege": 2},
        "modify": {"irreversibility": 2, "externality": 1, "privacy": 1, "privilege": 4},
        "delete": {"irreversibility": 8, "externality": 2, "privacy": 2, "privilege": 6},
        "send": {"irreversibility": 4, "externality": 8, "privacy": 4, "privilege": 4},
        "publish": {"irreversibility": 6, "externality": 10, "privacy": 6, "privilege": 8},
        "execute": {"irreversibility": 8, "externality": 8, "privacy": 4, "privilege": 10},
    }

    def evaluate(
        self,
        verb: str,
        audience: str = "",
        scope: str = "internal",
        data_class: str = "",
        quantity: Optional[int] = None,
        policy_overrides: Optional[Dict[str, float]] = None,
    ) -> ActionRisk:
        base_risk = self.OPERATION_RISK.get(
            verb, {"irreversibility": 5, "externality": 5, "privacy": 5, "privilege": 5}
        )
        
        risk = ActionRisk(
            level=RiskLevel.MEDIUM,
            irreversibility=base_risk.get("irreversibility", 0),
            externality=base_risk.get("externality", 0),
            financial=0.0,
            privacy=base_risk.get("privacy", 0),
            privilege=base_risk.get("privilege", 0),
            legal=0.0,
            uncertainty=0.0,
            blast_radius=0.0,
        )
        
        # Context adjustments
        if audience and audience not in ("requester", "self"):
            risk.externality += 4
        if scope == "external":
            risk.externality += 6
        if data_class in ("pii", "financial", "credentials"):
            risk.privacy += 6
            risk.legal += 4
        if quantity and quantity > 1000:
            risk.blast_radius += 4
        
        # Policy overrides
        if policy_overrides:
            for key, value in policy_overrides.items():
                if hasattr(risk, key):
                    setattr(risk, key, value)
        
        # Classify risk level
        total = risk.autonomy_cost
        if total < 5:
            risk.level = RiskLevel.LOW
        elif total < 15:
            risk.level = RiskLevel.MEDIUM
        elif total < 25:
            risk.level = RiskLevel.HIGH
        else:
            risk.level = RiskLevel.CRITICAL
        
        return risk


class AutonomyBudget:
    """
    Tracks and enforces risk-weighted autonomy limits.
    Replaces fixed hop counting with cumulative risk budgeting.
    """

    def __init__(self, budget_limit: float = 50.0):
        self.budget_limit = budget_limit
        self.consumed: float = 0.0
        self._actions: List[ActionRisk] = []

    def can_act(self, action_risk: ActionRisk) -> bool:
        return self.consumed + action_risk.autonomy_cost <= self.budget_limit

    def consume(self, action_risk: ActionRisk) -> bool:
        if not self.can_act(action_risk):
            return False
        self.consumed += action_risk.autonomy_cost
        self._actions.append(action_risk)
        return True

    def remaining(self) -> float:
        return max(0, self.budget_limit - self.consumed)

    def reset(self) -> None:
        self.consumed = 0.0
        self._actions.clear()

    def actions_count(self) -> int:
        return len(self._actions)