"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 5: Evaluation.
    Test suite for evaluation metrics and benchmark generators.
    See docs/ARCHITECTURE_v2.0.md, Sections 16-18.
"""
from humanist_core.evaluation import (
    ApprovalFatigueMetrics,
    ApprovalFatigueSimulator,
    BenchmarkDataset,
    DetailedMetrics,
    EvaluationMetrics,
    MockEnvelopeProcessor,
    PhaseMetrics,
    ViolationType,
    calculate_false_positive_rate,
    calculate_missed_boundary_rate,
    generate_evaluation_report,
    measure_runtime_overhead_detailed,
)


class TestDetailedMetrics:
    """Tests for DetailedMetrics."""

    def test_from_samples_empty(self):
        """Empty sample list is handled gracefully."""
        metrics = DetailedMetrics.from_samples([])
        assert metrics.mean == 0
        assert metrics.median == 0
        assert metrics.p95 == 0

    def test_from_samples_single(self):
        """Single-value sample list."""
        metrics = DetailedMetrics.from_samples([5.0])
        assert metrics.mean == 5.0
        assert metrics.median == 5.0
        assert metrics.std_dev == 0.0

    def test_from_samples_multiple(self):
        """Multi-value sample list."""
        metrics = DetailedMetrics.from_samples([1.0, 2.0, 3.0, 4.0, 5.0])
        assert metrics.mean == 3.0
        assert metrics.median == 3.0
        assert metrics.min_val == 1.0
        assert metrics.max_val == 5.0

    def test_percentiles(self):
        """Nearest-rank percentiles."""
        metrics = DetailedMetrics.from_samples(list(range(1, 101)))
        assert metrics.p95 == 95
        assert metrics.p99 == 99


class TestPhaseMetrics:
    """Tests for PhaseMetrics."""

    def test_calculate_perfect_detection(self):
        """Perfect detection yields 100% rate and 0% FPR."""
        pm = PhaseMetrics.calculate(1, 10, 0, 0, 100)
        assert pm.detection_rate == 100.0
        assert pm.false_positive_rate == 0.0

    def test_calculate_with_missed_violations(self):
        """Missed violations and false positives are counted."""
        pm = PhaseMetrics.calculate(2, 8, 2, 5, 100)
        assert pm.detection_rate == 80.0
        assert pm.false_positive_rate == 5.0

    def test_calculate_zero_divisions(self):
        """Zero denominators do not raise."""
        pm = PhaseMetrics.calculate(3, 0, 0, 0, 0)
        assert pm.detection_rate == 0.0
        assert pm.false_positive_rate == 0.0


class TestApprovalFatigueMetrics:
    """Tests for ApprovalFatigueMetrics."""

    def test_from_sessions_empty(self):
        """Empty session list is handled gracefully."""
        metrics = ApprovalFatigueMetrics.from_sessions([])
        assert metrics.total_sessions == 0
        assert metrics.avg_per_session == 0.0

    def test_from_sessions_constant(self):
        """Constant approval counts."""
        metrics = ApprovalFatigueMetrics.from_sessions([5, 5, 5, 5, 5])
        assert metrics.total_sessions == 5
        assert metrics.total_approvals == 25
        assert metrics.avg_per_session == 5.0
        assert metrics.max_per_session == 5
        assert metrics.min_per_session == 5

    def test_trend_calculation(self):
        """Linear growth yields slope 1.0."""
        metrics = ApprovalFatigueMetrics.from_sessions([1, 2, 3, 4, 5])
        assert metrics.trend == 1.0

    def test_trend_single_session(self):
        """A single session has no trend."""
        metrics = ApprovalFatigueMetrics.from_sessions([3])
        assert metrics.trend == 0.0

class TestBenchmarkDataset:
    """Tests for BenchmarkDataset."""

    def test_generate_balanced_dataset_size(self):
        """Dataset has the requested size."""
        dataset = BenchmarkDataset.generate_balanced_dataset(size=100)
        assert len(dataset.envelopes) == 100

    def test_generate_balanced_dataset_proportions(self):
        """Violation proportion is respected."""
        dataset = BenchmarkDataset.generate_balanced_dataset(size=1000, violation_rate=0.1)
        assert dataset.violation_count == 100
        assert dataset.legitimate_count == 900

    def test_legitimate_envelopes_are_legitimate(self):
        """Normal scenarios are flagged legitimate."""
        dataset = BenchmarkDataset.generate_balanced_dataset(size=100)
        for envelope in dataset.envelopes:
            if envelope.scenario_type is not None and envelope.scenario_type.value == "normal":
                assert envelope.is_legitimate is True

    def test_violation_envelopes_are_illegitimate(self):
        """Violation scenarios are flagged illegitimate."""
        dataset = BenchmarkDataset.generate_balanced_dataset(size=100, violation_rate=0.1)
        violations = [e for e in dataset.envelopes if e.scenario_type.value == "violation"]
        for envelope in violations:
            assert envelope.is_legitimate is False

    def test_reproducibility_with_seed(self):
        """Same seed produces the same dataset."""
        dataset1 = BenchmarkDataset.generate_balanced_dataset(seed=42)
        dataset2 = BenchmarkDataset.generate_balanced_dataset(seed=42)
        assert len(dataset1.envelopes) == len(dataset2.envelopes)
        for e1, e2 in zip(dataset1.envelopes[:10], dataset2.envelopes[:10]):
            assert e1.id == e2.id
            assert e1.intent == e2.intent


class TestApprovalFatigueSimulator:
    """Tests for ApprovalFatigueSimulator."""

    def test_simulate_sessions_count(self):
        """Requested number of sessions is returned."""
        sessions = ApprovalFatigueSimulator.simulate_sessions(num_sessions=50)
        assert len(sessions) == 50

    def test_simulate_sessions_positive_values(self):
        """Approval counts are non-negative."""
        sessions = ApprovalFatigueSimulator.simulate_sessions(num_sessions=100)
        assert all(count >= 0 for count in sessions)

    def test_fatigue_factor_increases_approvals(self):
        """Fatigue factor raises approval counts over time."""
        sessions = ApprovalFatigueSimulator.simulate_sessions(
            num_sessions=100, base_approval_rate=0.1, fatigue_factor=0.05
        )
        early_avg = sum(sessions[:10]) / 10
        late_avg = sum(sessions[-10:]) / 10
        assert late_avg > early_avg


class TestRuntimeOverhead:
    """Tests for runtime overhead measurement."""

    def test_measure_runtime_overhead(self):
        """Overhead is positive and percentiles are ordered."""
        processor = MockEnvelopeProcessor()
        dataset = BenchmarkDataset.generate_balanced_dataset(size=10)
        metrics = measure_runtime_overhead_detailed(processor, dataset.envelopes)
        assert metrics.mean > 0
        assert metrics.median > 0
        assert metrics.p99 >= metrics.p95


class TestMetricsCalculations:
    """Tests for rate calculation helpers."""

    def test_calculate_false_positive_rate(self):
        assert calculate_false_positive_rate(100, 5) == 5.0

    def test_calculate_false_positive_rate_zero_division(self):
        assert calculate_false_positive_rate(0, 0) == 0.0

    def test_calculate_missed_boundary_rate(self):
        assert calculate_missed_boundary_rate(100, 90) == 10.0

    def test_calculate_missed_boundary_rate_zero_division(self):
        assert calculate_missed_boundary_rate(0, 0) == 0.0


class TestEvaluationReport:
    """Tests for report generation."""

    def test_generate_evaluation_report(self):
        """Report contains all key sections."""
        dataset = BenchmarkDataset.generate_balanced_dataset(size=100, seed=42)
        processor = MockEnvelopeProcessor()
        runtime_metrics = measure_runtime_overhead_detailed(processor, dataset.envelopes[:10])

        phase_metrics = {
            1: PhaseMetrics.calculate(1, 10, 0, 2, 100),
            2: PhaseMetrics.calculate(2, 8, 2, 3, 100),
        }
        sessions = ApprovalFatigueSimulator.simulate_sessions(num_sessions=50)
        approval_metrics = ApprovalFatigueMetrics.from_sessions(sessions)

        metrics = EvaluationMetrics(
            runtime_overhead=runtime_metrics,
            false_positive_rate=2.5,
            missed_boundary_rate=10.0,
            approval_fatigue=approval_metrics,
            phase_metrics=phase_metrics,
            violations_by_type={},
        )
        report = generate_evaluation_report(metrics)

        assert "HACP v2.0 EVALUATION REPORT" in report
        assert "RUNTIME OVERHEAD" in report
        assert "ACCURACY METRICS" in report
        assert "APPROVAL FATIGUE" in report
        assert "PHASE BREAKDOWN" in report
        assert "END OF REPORT" in report

    def test_generate_evaluation_report_with_violation_types(self):
        """Violation type breakdown is rendered when present."""
        runtime = DetailedMetrics.from_samples([1.0, 2.0, 3.0])
        metrics = EvaluationMetrics(
            runtime_overhead=runtime,
            false_positive_rate=1.0,
            missed_boundary_rate=2.0,
            approval_fatigue=ApprovalFatigueMetrics.from_sessions([1, 2]),
            phase_metrics={},
            violations_by_type={ViolationType.SCOPE: 7},
        )
        report = generate_evaluation_report(metrics)
        assert "scope: 7" in report