"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 5: Evaluation.
    Synthetic benchmark scenarios and session simulators used to
    exercise the evaluation metrics.
    See docs/ARCHITECTURE_v2.0.md, Sections 16-18.
"""
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum
import random
import time
from datetime import datetime


class ScenarioType(Enum):
    """Kind of synthetic scenario."""
    NORMAL = "normal"
    EDGE_CASE = "edge_case"
    VIOLATION = "violation"


@dataclass
class SyntheticEnvelope:
    """Synthetic envelope used for benchmarking."""
    id: str
    intent: str
    scope: str
    authority_level: str
    risk_score: float
    is_legitimate: bool
    scenario_type: ScenarioType
    requires_approval: bool


@dataclass
class BenchmarkDataset:
    """Synthetic dataset with configurable violation/approval proportions."""
    envelopes: List[SyntheticEnvelope]
    legitimate_count: int
    violation_count: int
    approval_required_count: int

    @classmethod
    def generate_balanced_dataset(
        cls,
        size: int = 1000,
        violation_rate: float = 0.1,
        approval_rate: float = 0.2,
        seed: int = 42,
    ) -> "BenchmarkDataset":
        """Generate a reproducible dataset with the given proportions."""
        random.seed(seed)

        envelopes = []
        violation_count = int(size * violation_rate)
        legitimate_count = size - violation_count

        # Legitimate operations
        for i in range(legitimate_count):
            envelopes.append(cls._generate_legitimate_envelope(i, approval_rate))

        # Boundary violations
        for i in range(violation_count):
            envelopes.append(cls._generate_violation_envelope(legitimate_count + i))

        # Shuffle for realism
        random.shuffle(envelopes)

        approval_required = sum(1 for e in envelopes if e.requires_approval)

        return cls(
            envelopes=envelopes,
            legitimate_count=legitimate_count,
            violation_count=violation_count,
            approval_required_count=approval_required,
        )

    @staticmethod
    def _generate_legitimate_envelope(index: int, approval_rate: float) -> SyntheticEnvelope:
        """Generate a legitimate envelope."""
        intents = [
            "read_user_data", "write_user_data", "send_email",
            "access_external_api", "modify_configuration",
            "generate_report", "backup_database",
        ]
        scopes = [
            "user:profile", "user:settings", "system:config",
            "data:analytics", "communication:email",
        ]
        authority_levels = ["user", "admin", "system"]

        intent = random.choice(intents)
        scope = random.choice(scopes)
        authority = random.choice(authority_levels)

        # Base risk depends on the operation
        base_risk = {
            "read_user_data": 0.1,
            "write_user_data": 0.4,
            "send_email": 0.3,
            "access_external_api": 0.5,
            "modify_configuration": 0.7,
            "generate_report": 0.2,
            "backup_database": 0.6,
        }[intent]

        risk_score = max(0.0, min(1.0, base_risk + random.uniform(-0.1, 0.1)))

        # High-risk operations always require approval
        requires_approval = risk_score > 0.6 or random.random() < approval_rate

        return SyntheticEnvelope(
            id=f"legit_{index:06d}",
            intent=intent,
            scope=scope,
            authority_level=authority,
            risk_score=risk_score,
            is_legitimate=True,
            scenario_type=ScenarioType.NORMAL,
            requires_approval=requires_approval,
        )

    @staticmethod
    def _generate_violation_envelope(index: int) -> SyntheticEnvelope:
        """Generate an envelope that violates HACP boundaries."""
        violation_types = [
            # Authority violations (Phase 1)
            {"intent": "delete_all_data", "scope": "system:*", "authority": "user"},
            {"intent": "access_admin_panel", "scope": "admin:config", "authority": "user"},
            # Scope violations (Phase 2)
            {"intent": "read_user_data", "scope": "other_user:private", "authority": "user"},
            {"intent": "modify_configuration", "scope": "production:*", "authority": "admin"},
            # Provenance violations (Phase 3)
            {"intent": "bypass_audit_log", "scope": "system:logs", "authority": "system"},
            {"intent": "tamper_evidence", "scope": "security:*", "authority": "admin"},
        ]
        violation = random.choice(violation_types)

        return SyntheticEnvelope(
            id=f"violation_{index:06d}",
            intent=violation["intent"],
            scope=violation["scope"],
            authority_level=violation["authority"],
            risk_score=random.uniform(0.8, 1.0),
            is_legitimate=False,
            scenario_type=ScenarioType.VIOLATION,
            requires_approval=False,
        )


class ApprovalFatigueSimulator:
    """Simulates user sessions to measure approval fatigue."""

    @staticmethod
    def simulate_sessions(
        num_sessions: int = 100,
        avg_actions_per_session: int = 20,
        base_approval_rate: float = 0.15,
        fatigue_factor: float = 0.02,
        seed: int = 42,
    ) -> List[int]:
        """
        Simulate user sessions.

        Args:
            num_sessions: number of sessions to simulate.
            avg_actions_per_session: mean actions per session.
            base_approval_rate: base probability of an approval request.
            fatigue_factor: approval-rate growth per session (fatigue).
            seed: seed for reproducibility.

        Returns:
            Per-session approval counts.
        """
        random.seed(seed)
        session_approvals = []

        for session_idx in range(num_sessions):
            num_actions = int(random.gauss(avg_actions_per_session, 5))
            num_actions = max(5, min(50, num_actions))

            # Approval pressure grows as the user gets tired
            current_approval_rate = min(0.8, base_approval_rate + session_idx * fatigue_factor)

            approvals = sum(
                1 for _ in range(num_actions) if random.random() < current_approval_rate
            )
            session_approvals.append(approvals)

        return session_approvals


class MockEnvelopeProcessor:
    """Mock processor used to measure runtime overhead."""

    def process_without_checks(self, envelope: SyntheticEnvelope) -> Dict:
        """Baseline processing without HACP checks."""
        return {
            "status": "processed",
            "envelope_id": envelope.id,
            "timestamp": datetime.now().isoformat(),
        }

    def process_with_checks(self, envelope: SyntheticEnvelope) -> Dict:
        """Processing with simulated HACP check latency."""
        # Phase 1: authority check
        time.sleep(0.001)
        # Phase 2: scope validation
        time.sleep(0.0015)
        # Phase 3: provenance verification
        time.sleep(0.002)
        # Phase 4: policy digest
        time.sleep(0.001)

        return {
            "status": "processed",
            "envelope_id": envelope.id,
            "timestamp": datetime.now().isoformat(),
            "hacp_verified": True,
        }