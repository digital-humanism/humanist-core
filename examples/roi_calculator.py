"""
    humanist-core SDK
    Copyright (C) 2026 Sten & Digital Humanism Initiative
    Licensed under AGPLv3

    HACP v2.0 — ROI Calculator for Enterprise Sales Demos.
    Quantifies financial impact of deploying Human Agency Continuity Protocol.
    Pricing model: perpetual license (CAPEX) + annual support (OPEX), priced so
    the client hits a target ROI on capital (Oracle/SAP/IBM playbook).
    See COMMERCIAL.md for licensing and business case details.
"""
import argparse
import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class ROIInputs:
    """Input parameters for ROI calculation."""
    # Business parameters
    transactions_per_day: int
    avg_transaction_value: float  # USD
    incident_probability: float   # 0.0 to 1.0
    avg_incident_cost: float      # USD
    analyst_salary: float         # USD per year

    # Technical parameters (from Phase 5 evaluation)
    detection_rate: float         # 0.0 to 1.0
    false_positive_rate: float    # 0.0 to 1.0
    runtime_overhead_ms: float    # milliseconds per transaction
    approvals_per_session: float  # average approvals per session
    review_minutes_per_fp: float  # analyst minutes per false-positive review

    # Commercial parameters
    license_capex: float          # one-time perpetual license, USD
    support_rate: float           # annual support as fraction of license
    target_roi: float             # client target ROI on CAPEX, percent
    horizon_years: int            # TCO horizon, years
    inflation: float              # annual inflation, percent
    uplift_extra: float           # extra uplift on top of inflation, percent


@dataclass
class ROIResults:
    """Output of ROI calculation."""
    # Baseline (without humanist-core)
    annual_transactions: int
    annual_incidents_without_guard: float
    annual_loss_without_guard: float

    # With humanist-core
    annual_incidents_with_guard: float
    annual_loss_with_guard: float
    annual_false_positive_cost: float
    annual_fp_count: float
    reviewer_fte: float

    # Financial impact
    annual_savings: float             # gross annual benefit G
    support_y1: float                 # annual support OPEX
    annual_net_benefit: float         # G - support
    roi_percentage: float             # ROI on CAPEX
    payback_years: Optional[float]
    breakeven_incident_probability: float

    # Commercial terms
    slots_required: int
    uplift_pct: float
    tco: float                        # capex + support over horizon
    gross_total: float                # G * horizon
    net_total: float                  # gross_total - tco

    # Operational metrics
    total_runtime_overhead_hours: float
    approval_fatigue_indicator: str


# Market-norm payback used for the breakeven honesty anchor, years
BREAKEVEN_PAYBACK_YEARS = 10.0


def calculate_roi(inputs: ROIInputs) -> ROIResults:
    """Calculate ROI for humanist-core deployment (CAPEX/OPEX model)."""
    # Baseline calculations (without humanist-core)
    annual_transactions = inputs.transactions_per_day * 365
    annual_incidents_without_guard = annual_transactions * inputs.incident_probability
    annual_loss_without_guard = annual_incidents_without_guard * inputs.avg_incident_cost

    # With humanist-core
    annual_incidents_with_guard = (
        annual_incidents_without_guard * (1 - inputs.detection_rate)
    )
    annual_loss_with_guard = annual_incidents_with_guard * inputs.avg_incident_cost

    # False positive cost: analyst time to review flagged transactions
    analyst_hourly_rate = inputs.analyst_salary / 2080.0  # 2080 working hours/year
    annual_fp_count = annual_transactions * inputs.false_positive_rate
    annual_false_positive_cost = (
        annual_fp_count * (inputs.review_minutes_per_fp / 60.0) * analyst_hourly_rate
    )
    reviewer_fte = (annual_fp_count * (inputs.review_minutes_per_fp / 60.0)) / 2080.0

    # Total runtime overhead in hours per year
    total_overhead_ms = annual_transactions * inputs.runtime_overhead_ms
    total_runtime_overhead_hours = total_overhead_ms / (1000 * 60 * 60)

    # Gross annual benefit
    annual_savings = (
        annual_loss_without_guard
        - annual_loss_with_guard
        - annual_false_positive_cost
    )

    # Commercial math: license is CAPEX, support is OPEX
    support_y1 = inputs.license_capex * inputs.support_rate
    annual_net_benefit = annual_savings - support_y1

    if inputs.license_capex > 0:
        roi_percentage = (annual_net_benefit / inputs.license_capex) * 100
        payback_years = (
            inputs.license_capex / annual_net_benefit
            if annual_net_benefit > 0 else None
        )
    else:
        roi_percentage = float('inf')
        payback_years = None

    # Multi-year cash view: capex upfront, support with annual uplift
    uplift_pct = inputs.inflation + inputs.uplift_extra
    tco = inputs.license_capex
    support_y = support_y1
    for _ in range(inputs.horizon_years):
        tco += support_y
        support_y *= 1 + uplift_pct / 100
    gross_total = annual_savings * inputs.horizon_years
    net_total = gross_total - tco

    # Honesty anchor: incident rate at which payback hits the market norm
    if (
        inputs.license_capex > 0
        and inputs.detection_rate > 0
        and inputs.avg_incident_cost > 0
        and annual_transactions > 0
    ):
        required_net = inputs.license_capex / BREAKEVEN_PAYBACK_YEARS
        required_gross = required_net + support_y1
        be_incidents = (
            (required_gross + annual_false_positive_cost)
            / (inputs.detection_rate * inputs.avg_incident_cost)
        )
        breakeven_incident_probability = be_incidents / annual_transactions
    else:
        breakeven_incident_probability = 0.0

    # Capacity Units: one unit per 50K transactions/day
    slots_required = max(1, math.ceil(inputs.transactions_per_day / 50000))

    # Approval fatigue indicator
    if inputs.approvals_per_session < 10:
        fatigue_indicator = "Low (excellent UX)"
    elif inputs.approvals_per_session < 20:
        fatigue_indicator = "Moderate (acceptable)"
    else:
        fatigue_indicator = "High (consider UX optimization)"

    return ROIResults(
        annual_transactions=annual_transactions,
        annual_incidents_without_guard=annual_incidents_without_guard,
        annual_loss_without_guard=annual_loss_without_guard,
        annual_incidents_with_guard=annual_incidents_with_guard,
        annual_loss_with_guard=annual_loss_with_guard,
        annual_false_positive_cost=annual_false_positive_cost,
        annual_fp_count=annual_fp_count,
        reviewer_fte=reviewer_fte,
        annual_savings=annual_savings,
        support_y1=support_y1,
        annual_net_benefit=annual_net_benefit,
        roi_percentage=roi_percentage,
        payback_years=payback_years,
        breakeven_incident_probability=breakeven_incident_probability,
        slots_required=slots_required,
        uplift_pct=uplift_pct,
        tco=tco,
        gross_total=gross_total,
        net_total=net_total,
        total_runtime_overhead_hours=total_runtime_overhead_hours,
        approval_fatigue_indicator=fatigue_indicator,
    )


def format_currency(value: float) -> str:
    """Format number as USD currency."""
    sign = "-" if value < 0 else ""
    v = abs(value)
    if v >= 1_000_000:
        return f"{sign}${v / 1_000_000:.2f}M"
    elif v >= 1_000:
        return f"{sign}${v / 1_000:.2f}K"
    else:
        return f"{sign}${v:.2f}"


def validate_inputs(inputs: ROIInputs, results: ROIResults) -> list:
    """Validate input parameters and return warnings."""
    warnings = []

    if inputs.incident_probability > 0.001:
        warnings.append(
            f"WARNING: incident_probability {inputs.incident_probability*100:.2f}% is very high. "
            "Typical enterprise systems have 0.0001-0.001% (0.000001-0.00001)."
        )

    if results.annual_loss_without_guard > 100_000_000:
        warnings.append(
            f"WARNING: Annual loss exposure {format_currency(results.annual_loss_without_guard)} "
            "is extremely high. Consider if incident_probability is realistic."
        )

    if inputs.false_positive_rate > 0.1:
        warnings.append(
            f"WARNING: false_positive_rate {inputs.false_positive_rate*100:.1f}% is high. "
            "Values >10% significantly impact ROI."
        )

    if results.reviewer_fte > 5:
        warnings.append(
            f"WARNING: FP volume requires {results.reviewer_fte:.1f} full-time reviewers. "
            "Consider tuning detection thresholds or auto-approving low-risk scopes."
        )

    if 0 < results.roi_percentage < 5:
        warnings.append(
            "WARNING: ROI on CAPEX below 5% — under typical corporate hurdle rates "
            "(10-15%). Capital approval may be hard; consider a lower license."
        )

    if results.roi_percentage > 10000:
        warnings.append(
            "WARNING: ROI > 10,000% — license price is unrealistically low "
            "for this volume."
        )

    return warnings


def generate_roi_report(inputs: ROIInputs, results: ROIResults) -> str:
    """Generate human-readable ROI report."""
    report = [
        "=" * 70,
        "HUMANIST-CORE ROI ANALYSIS",
        "=" * 70,
        "",
        "INPUT PARAMETERS",
        "-" * 70,
        f"Transactions per day: {inputs.transactions_per_day:,}",
        f"Average transaction value: {format_currency(inputs.avg_transaction_value)}",
        f"Incident probability: {inputs.incident_probability * 100:.4f}%",
        f"Average incident cost: {format_currency(inputs.avg_incident_cost)}",
        f"Client target ROI on CAPEX: {inputs.target_roi:.1f}%",
        "",
        "TECHNICAL PARAMETERS (Phase 5)",
        "-" * 70,
        f"Detection rate: {inputs.detection_rate * 100:.1f}%",
        f"False positive rate: {inputs.false_positive_rate * 100:.2f}%",
        f"Runtime overhead: {inputs.runtime_overhead_ms:.2f} ms per transaction",
        f"Approvals per session: {inputs.approvals_per_session:.2f}",
        "",
        "BASELINE (WITHOUT HUMANIST-CORE)",
        "-" * 70,
        f"Annual transactions: {results.annual_transactions:,}",
        f"Expected incidents/year: {results.annual_incidents_without_guard:.1f}",
        f"Annual loss exposure: {format_currency(results.annual_loss_without_guard)}",
        "",
        "WITH HUMANIST-CORE",
        "-" * 70,
        f"Prevented incidents: {results.annual_incidents_without_guard - results.annual_incidents_with_guard:.1f}",
        f"Remaining incidents/year: {results.annual_incidents_with_guard:.1f}",
        f"Annual loss with guard: {format_currency(results.annual_loss_with_guard)}",
        f"False positives flagged/year: {results.annual_fp_count:,.0f}",
        f"FP review cost (analyst time): {format_currency(results.annual_false_positive_cost)}",
        f"Reviewer headcount: {results.reviewer_fte:.1f} FTE",
        f"Runtime overhead: {results.total_runtime_overhead_hours:.1f} hours/year",
        "",
        "FINANCIAL IMPACT",
        "-" * 70,
        f"Gross annual savings: {format_currency(results.annual_savings)}",
        f"Support Y1 (OPEX): {format_currency(results.support_y1)}",
        f"Annual net benefit: {format_currency(results.annual_net_benefit)}",
    ]

    if results.roi_percentage != float('inf'):
        report.append(f"ROI on CAPEX: {results.roi_percentage:.1f}%")

    if results.payback_years is not None:
        report.append(f"Payback: {results.payback_years:.1f} years (static, excl. uplift)")
    else:
        report.append("Payback: never at current assumptions")

    if results.breakeven_incident_probability > 0 and inputs.incident_probability > 0:
        margin = inputs.incident_probability / results.breakeven_incident_probability
        report.append(
            f"Breakeven incident rate ({BREAKEVEN_PAYBACK_YEARS:.0f}-yr payback): "
            f"{results.breakeven_incident_probability * 100:.4f}% "
            f"(your assumption is {margin:.1f}x above)"
        )

    report.extend([
        "",
        f"COMMERCIAL TERMS ({inputs.horizon_years}-YEAR HORIZON)",
        "-" * 70,
        f"Capacity Units: {results.slots_required} "
        f"(50K tpd / {results.reviewer_fte:.1f} FTE / "
        f"{inputs.approvals_per_session:.2f} approvals per session)",
        f"License (perpetual, CAPEX): {format_currency(inputs.license_capex)}",
        f"Support Y1 ({inputs.support_rate * 100:.0f}% of license, OPEX): "
        f"{format_currency(results.support_y1)}",
        f"Annual uplift from Y2: {results.uplift_pct:.1f}% (CPI + 1.5%)",
        f"{inputs.horizon_years}-year TCO: {format_currency(results.tco)}",
        f"{inputs.horizon_years}-year gross savings: {format_currency(results.gross_total)}",
        "Note: avoided losses do not appear in P&L; evaluate as balance-sheet protection.",
        "Unlimited License Agreement (ULA): negotiated separately "
        "(2-3 yr term, certification at term end)",
        "",
        "OPERATIONAL METRICS",
        "-" * 70,
        f"Approval fatigue: {results.approval_fatigue_indicator}",
        "",
    ])

    # Validation warnings (standalone block)
    warnings = validate_inputs(inputs, results)
    if warnings:
        report.append("VALIDATION WARNINGS")
        report.append("-" * 70)
        report.extend(warnings)
        report.append("")

    # Recommendation
    if results.annual_net_benefit > 0 and results.roi_percentage >= 10:
        report.append("RECOMMENDATION: Solid ROI - proceed with deployment")
    elif results.annual_net_benefit > 0:
        report.append("RECOMMENDATION: Positive ROI - consider pilot deployment")
    else:
        report.append("RECOMMENDATION: Negative ROI - review incident cost assumptions")

    report.extend([
        "",
        "=" * 70,
    ])

    return "\n".join(report)


def main():
    """CLI entry point for ROI calculator."""
    parser = argparse.ArgumentParser(
        description="Calculate ROI for humanist-core deployment (CAPEX/OPEX model)"
    )

    # Business parameters
    parser.add_argument(
        "--transactions-per-day", type=int, default=50000,
        help="Number of transactions per day (default: 50000)"
    )
    parser.add_argument(
        "--avg-transaction-value", type=float, default=50.0,
        help="Average transaction value in USD (default: 50.0)"
    )
    parser.add_argument(
        "--incident-probability", type=float, default=0.00001,
        help="Probability of incident per transaction (default: 0.00001)"
    )
    parser.add_argument(
        "--avg-incident-cost", type=float, default=100000.0,
        help="Average cost of security incident in USD (default: 100000.0)"
    )
    parser.add_argument(
        "--analyst-salary", type=float, default=120000.0,
        help="Analyst salary USD/year (default: 120000.0)"
    )
    parser.add_argument(
        "--review-minutes", type=float, default=3.0,
        help="Analyst minutes per false-positive review (default: 3.0)"
    )

    # Commercial parameters
    parser.add_argument(
        "--license-capex", type=float, default=None,
        help="Explicit one-time license in USD (overrides target-ROI pricing)"
    )
    parser.add_argument(
        "--target-roi", type=float, default=12.0,
        help="Client target ROI on CAPEX, %% (default: 12.0; band 10-15)"
    )
    parser.add_argument(
        "--support-rate", type=float, default=0.15,
        help="Annual support as fraction of license (default: 0.15)"
    )
    parser.add_argument(
        "--inflation", type=float, default=3.0,
        help="Annual inflation, %% (default: 3.0)"
    )
    parser.add_argument(
        "--uplift-extra", type=float, default=1.5,
        help="Extra uplift on top of inflation from Y2, %% (default: 1.5)"
    )
    parser.add_argument(
        "--years", type=int, default=3,
        help="TCO horizon in years (default: 3)"
    )

    # Technical parameters (Phase 5 defaults)
    parser.add_argument(
        "--detection-rate", type=float, default=0.90,
        help="Detection rate 0.0-1.0 (default: 0.90 from Phase 5)"
    )
    parser.add_argument(
        "--false-positive-rate", type=float, default=0.0207,
        help="False positive rate 0.0-1.0 (default: 0.0207 from Phase 5)"
    )
    parser.add_argument(
        "--runtime-overhead-ms", type=float, default=6.4,
        help="Runtime overhead in ms (default: 6.4 from Phase 5)"
    )
    parser.add_argument(
        "--approvals-per-session", type=float, default=13.85,
        help="Approvals per session (default: 13.85 from Phase 5)"
    )

    args = parser.parse_args()

    common = dict(
        transactions_per_day=args.transactions_per_day,
        avg_transaction_value=args.avg_transaction_value,
        incident_probability=args.incident_probability,
        avg_incident_cost=args.avg_incident_cost,
        analyst_salary=args.analyst_salary,
        review_minutes_per_fp=args.review_minutes,
        detection_rate=args.detection_rate,
        false_positive_rate=args.false_positive_rate,
        runtime_overhead_ms=args.runtime_overhead_ms,
        approvals_per_session=args.approvals_per_session,
        support_rate=args.support_rate,
        target_roi=args.target_roi,
        horizon_years=args.years,
        inflation=args.inflation,
        uplift_extra=args.uplift_extra,
    )

    # Pricing: explicit capex override, or value-based default.
    # L = G / (r + support_rate) prices the license so the client hits
    # exactly the target ROI on capital.
    if args.license_capex is not None:
        license_capex = args.license_capex
    else:
        pre = calculate_roi(ROIInputs(license_capex=0.0, **common))
        license_capex = max(
            0.0,
            pre.annual_savings / (args.target_roi / 100.0 + args.support_rate),
        )

    inputs = ROIInputs(license_capex=license_capex, **common)

    results = calculate_roi(inputs)
    report = generate_roi_report(inputs, results)

    print(report)

    # Save to file
    with open("roi_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("\nReport saved to roi_report.txt")


if __name__ == "__main__":
    main()