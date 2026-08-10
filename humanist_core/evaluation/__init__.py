"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 5: Evaluation.
    Public API of the evaluation subpackage.
    See docs/ARCHITECTURE_v2.0.md, Sections 16-18.
"""
from humanist_core.evaluation.metrics import (
    ApprovalFatigueMetrics,
    DetailedMetrics,
    EvaluationMetrics,
    PhaseMetrics,
    ViolationType,
    calculate_false_positive_rate,
    calculate_missed_boundary_rate,
    generate_evaluation_report,
    measure_runtime_overhead_detailed,
)
from humanist_core.evaluation.benchmark import (
    ApprovalFatigueSimulator,
    BenchmarkDataset,
    MockEnvelopeProcessor,
    ScenarioType,
    SyntheticEnvelope,
)

__all__ = [
    # Metrics
    "EvaluationMetrics",
    "DetailedMetrics",
    "PhaseMetrics",
    "ApprovalFatigueMetrics",
    "ViolationType",
    "measure_runtime_overhead_detailed",
    "calculate_false_positive_rate",
    "calculate_missed_boundary_rate",
    "generate_evaluation_report",
    # Benchmark
    "BenchmarkDataset",
    "ApprovalFatigueSimulator",
    "MockEnvelopeProcessor",
    "SyntheticEnvelope",
    "ScenarioType",
]