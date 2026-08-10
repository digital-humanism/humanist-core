"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 5: Evaluation.
    Effectiveness metrics: false-positive rate, missed boundaries,
    approval fatigue and runtime overhead.
    See docs/ARCHITECTURE_v2.0.md, Sections 16-18.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from enum import Enum
import math
import statistics
import time
from datetime import datetime


class ViolationType(Enum):
    """Categories of HACP boundary violations."""
    AUTHORITY = "authority"    # Phase 1: IntentEnvelope violations
    SCOPE = "scope"            # Phase 2: SemanticDeltaGuard violations
    PROVENANCE = "provenance"  # Phase 3: ProvenanceGraph violations
    POLICY = "policy"          # Phase 4: PolicyDigest violations


@dataclass
class DetailedMetrics:
    """Summary statistics with percentiles and confidence intervals."""
    mean: float
    median: float
    p95: float
    p99: float
    std_dev: float
    min_val: float
    max_val: float
    confidence_interval_95: Tuple[float, float]

    @classmethod
    def from_samples(cls, samples: List[float]) -> "DetailedMetrics":
        """Build DetailedMetrics from a list of measurements."""
        if not samples:
            return cls(0, 0, 0, 0, 0, 0, 0, (0, 0))

        sorted_samples = sorted(samples)
        n = len(samples)
        mean = statistics.mean(samples)
        median = statistics.median(samples)
        std_dev = statistics.stdev(samples) if n > 1 else 0.0

        # Percentiles (nearest-rank method)
        p95_rank = math.ceil(0.95 * n)
        p99_rank = math.ceil(0.99 * n)
        p95 = sorted_samples[min(p95_rank - 1, n - 1)]
        p99 = sorted_samples[min(p99_rank - 1, n - 1)]

        # 95% confidence interval of the mean
        margin = 1.96 * (std_dev / math.sqrt(n)) if n > 1 else 0.0
        ci_95 = (mean - margin, mean + margin)

        return cls(
            mean=mean,
            median=median,
            p95=p95,
            p99=p99,
            std_dev=std_dev,
            min_val=min(samples),
            max_val=max(samples),
            confidence_interval_95=ci_95,
        )


@dataclass
class PhaseMetrics:
    """Detection metrics for a single HACP phase."""
    phase: int  # 1-4
    violations_detected: int
    violations_missed: int
    false_positives: int
    legitimate_actions: int
    detection_rate: float
    false_positive_rate: float

    @classmethod
    def calculate(
        cls,
        phase: int,
        violations_detected: int,
        violations_missed: int,
        false_positives: int,
        legitimate_actions: int,
    ) -> "PhaseMetrics":
        """Compute detection and false-positive rates for one phase."""
        total_violations = violations_detected + violations_missed
        detection_rate = (
            (violations_detected / total_violations * 100) if total_violations > 0 else 0.0
        )
        fpr = (
            (false_positives / legitimate_actions * 100) if legitimate_actions > 0 else 0.0
        )

        return cls(
            phase=phase,
            violations_detected=violations_detected,
            violations_missed=violations_missed,
            false_positives=false_positives,
            legitimate_actions=legitimate_actions,
            detection_rate=detection_rate,
            false_positive_rate=fpr,
        )


@dataclass
class ApprovalFatigueMetrics:
    """Approval fatigue metrics with temporal tracking."""
    total_sessions: int
    total_approvals: int
    avg_per_session: float
    max_per_session: int
    min_per_session: int
    trend: float  # slope of approvals/session over time

    @classmethod
    def from_sessions(cls, session_approvals: List[int]) -> "ApprovalFatigueMetrics":
        """Compute fatigue metrics from per-session approval counts."""
        if not session_approvals:
            return cls(0, 0, 0.0, 0, 0, 0.0)

        total_sessions = len(session_approvals)
        total_approvals = sum(session_approvals)

        return cls(
            total_sessions=total_sessions,
            total_approvals=total_approvals,
            avg_per_session=total_approvals / total_sessions,
            max_per_session=max(session_approvals),
            min_per_session=min(session_approvals),
            trend=cls._calculate_trend(session_approvals),
        )

    @staticmethod
    def _calculate_trend(approvals: List[int]) -> float:
        """Linear regression slope of approvals over sessions."""
        if len(approvals) < 2:
            return 0.0

        n = len(approvals)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(approvals) / n

        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, approvals))
        denominator = sum((xi - x_mean) ** 2 for xi in x)

        return numerator / denominator if denominator > 0 else 0.0


@dataclass
class EvaluationMetrics:
    """Full HACP v2.0 evaluation result."""
    runtime_overhead: DetailedMetrics
    false_positive_rate: float
    missed_boundary_rate: float
    approval_fatigue: ApprovalFatigueMetrics
    phase_metrics: Dict[int, PhaseMetrics]
    violations_by_type: Dict[ViolationType, int]
    timestamp: datetime = field(default_factory=datetime.now)


def measure_runtime_overhead_detailed(
    envelope_processor,
    test_envelopes: List,
) -> DetailedMetrics:
    """Measure per-envelope runtime overhead introduced by HACP checks (ms)."""
    # Baseline: processing without HACP checks
    baseline_times = []
    for env in test_envelopes:
        start = time.perf_counter()
        envelope_processor.process_without_checks(env)
        baseline_times.append(time.perf_counter() - start)

    # HACP enabled
    hacp_times = []
    for env in test_envelopes:
        start = time.perf_counter()
        envelope_processor.process_with_checks(env)
        hacp_times.append(time.perf_counter() - start)

    # Per-envelope overhead in milliseconds
    overhead_samples = [(h - b) * 1000 for h, b in zip(hacp_times, baseline_times)]

    return DetailedMetrics.from_samples(overhead_samples)


def calculate_false_positive_rate(legitimate_actions: int, blocked_legitimate: int) -> float:
    """Percentage of legitimate actions incorrectly blocked."""
    if legitimate_actions == 0:
        return 0.0
    return (blocked_legitimate / legitimate_actions) * 100


def calculate_missed_boundary_rate(total_violations: int, caught_violations: int) -> float:
    """Percentage of boundary violations the system failed to detect."""
    if total_violations == 0:
        return 0.0
    missed = total_violations - caught_violations
    return (missed / total_violations) * 100


def generate_evaluation_report(metrics: EvaluationMetrics) -> str:
    """Render a human-readable evaluation report."""
    report = [
        "=" * 70,
        "HACP v2.0 EVALUATION REPORT",
        f"Generated: {metrics.timestamp.isoformat()}",
        "=" * 70,
        "",
        "RUNTIME OVERHEAD",
        "-" * 70,
        f"Mean: {metrics.runtime_overhead.mean:.2f} ms",
        f"Median (P50): {metrics.runtime_overhead.median:.2f} ms",
        f"P95: {metrics.runtime_overhead.p95:.2f} ms",
        f"P99: {metrics.runtime_overhead.p99:.2f} ms",
        f"Std Dev: {metrics.runtime_overhead.std_dev:.2f} ms",
        f"95% CI: [{metrics.runtime_overhead.confidence_interval_95[0]:.2f}, "
        f"{metrics.runtime_overhead.confidence_interval_95[1]:.2f}] ms",
        "",
        "ACCURACY METRICS",
        "-" * 70,
        f"False Positive Rate: {metrics.false_positive_rate:.2f}%",
        f"Missed Boundary Rate: {metrics.missed_boundary_rate:.2f}%",
        "",
        "APPROVAL FATIGUE",
        "-" * 70,
        f"Total Sessions: {metrics.approval_fatigue.total_sessions}",
        f"Total Approvals: {metrics.approval_fatigue.total_approvals}",
        f"Avg per Session: {metrics.approval_fatigue.avg_per_session:.2f}",
        f"Max per Session: {metrics.approval_fatigue.max_per_session}",
        f"Min per Session: {metrics.approval_fatigue.min_per_session}",
        f"Trend: {metrics.approval_fatigue.trend:+.2f} approvals/session",
        "",
        "PHASE BREAKDOWN",
        "-" * 70,
    ]

    for phase in sorted(metrics.phase_metrics.keys()):
        pm = metrics.phase_metrics[phase]
        report.extend([
            f"Phase {pm.phase}:",
            f"  Detection Rate: {pm.detection_rate:.2f}%",
            f"  False Positive Rate: {pm.false_positive_rate:.2f}%",
            f"  Violations Detected: {pm.violations_detected}",
            f"  Violations Missed: {pm.violations_missed}",
        ])

    report.extend(["", "VIOLATIONS BY TYPE", "-" * 70])
    for vtype, count in metrics.violations_by_type.items():
        report.append(f"{vtype.value}: {count}")

    report.extend(["", "=" * 70, "END OF REPORT", "=" * 70])

    return "\n".join(report)