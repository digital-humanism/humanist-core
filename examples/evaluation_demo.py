"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — Phase 5: Evaluation.
    End-to-end example: generate benchmark data, measure overhead and
    print a full evaluation report.
    See docs/ARCHITECTURE_v2.0.md, Sections 16-18.
"""
from humanist_core.evaluation import (
    ApprovalFatigueMetrics,
    ApprovalFatigueSimulator,
    BenchmarkDataset,
    EvaluationMetrics,
    MockEnvelopeProcessor,
    PhaseMetrics,
    ViolationType,
    calculate_false_positive_rate,
    calculate_missed_boundary_rate,
    generate_evaluation_report,
    measure_runtime_overhead_detailed,
)


def main() -> None:
    """Run the evaluation demo and save the report."""
    print("=" * 70)
    print("HACP v2.0 Evaluation Demo")
    print("=" * 70)
    print()

    # 1. Generate the synthetic dataset
    print("1. Generating synthetic benchmark dataset...")
    dataset = BenchmarkDataset.generate_balanced_dataset(
        size=1000,
        violation_rate=0.10,  # 10% violations
        approval_rate=0.20,   # 20% require approval
        seed=42,
    )
    print(f"   - {len(dataset.envelopes)} envelopes")
    print(f"   - {dataset.legitimate_count} legitimate actions")
    print(f"   - {dataset.violation_count} violations")
    print(f"   - {dataset.approval_required_count} require approval")
    print()

    # 2. Measure runtime overhead on a sample
    print("2. Measuring runtime overhead...")
    processor = MockEnvelopeProcessor()
    runtime_metrics = measure_runtime_overhead_detailed(processor, dataset.envelopes[:100])
    print(f"   - Mean overhead: {runtime_metrics.mean:.2f} ms")
    print(f"   - P50 (median): {runtime_metrics.median:.2f} ms")
    print(f"   - P95: {runtime_metrics.p95:.2f} ms")
    print(f"   - P99: {runtime_metrics.p99:.2f} ms")
    print()

    # 3. Simulate approval fatigue
    print("3. Simulating user sessions for approval fatigue...")
    sessions = ApprovalFatigueSimulator.simulate_sessions(
        num_sessions=100,
        avg_actions_per_session=20,
        base_approval_rate=0.15,
        fatigue_factor=0.02,
        seed=42,
    )
    approval_metrics = ApprovalFatigueMetrics.from_sessions(sessions)
    print(f"   - Total sessions: {approval_metrics.total_sessions}")
    print(f"   - Avg approvals/session: {approval_metrics.avg_per_session:.2f}")
    print(f"   - Trend: {approval_metrics.trend:+.2f} (positive = growing fatigue)")
    print()

    # 4. Per-phase detection metrics (simulated detector results)
    print("4. Calculating phase metrics...")
    phase_metrics = {
        1: PhaseMetrics.calculate(1, 95, 5, 20, 900),   # Authority
        2: PhaseMetrics.calculate(2, 90, 10, 27, 900),  # Scope
        3: PhaseMetrics.calculate(3, 85, 15, 9, 900),   # Provenance
    }
    for phase, pm in phase_metrics.items():
        print(f"   - Phase {phase}: {pm.detection_rate:.1f}% detection, "
              f"{pm.false_positive_rate:.1f}% FPR")
    print()

    # 5. Aggregate metrics
    print("5. Calculating aggregate metrics...")
    total_legitimate = 900 * len(phase_metrics)
    total_false_positives = sum(pm.false_positives for pm in phase_metrics.values())
    total_violations = 100 * len(phase_metrics)
    total_caught = sum(pm.violations_detected for pm in phase_metrics.values())

    fpr = calculate_false_positive_rate(total_legitimate, total_false_positives)
    missed_rate = calculate_missed_boundary_rate(total_violations, total_caught)
    print(f"   - Overall FPR: {fpr:.2f}%")
    print(f"   - Missed boundary rate: {missed_rate:.2f}%")
    print()

    # 6. Generate and save the final report
    print("6. Generating evaluation report...")
    evaluation_metrics = EvaluationMetrics(
        runtime_overhead=runtime_metrics,
        false_positive_rate=fpr,
        missed_boundary_rate=missed_rate,
        approval_fatigue=approval_metrics,
        phase_metrics=phase_metrics,
        violations_by_type={
            ViolationType.AUTHORITY: 95,
            ViolationType.SCOPE: 90,
            ViolationType.PROVENANCE: 85,
        },
    )
    report = generate_evaluation_report(evaluation_metrics)
    print()
    print(report)

    with open("evaluation_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("Report saved to evaluation_report.txt")


if __name__ == "__main__":
    main()