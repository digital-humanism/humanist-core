# humanist-core SDK

![tests](https://github.com/digital-humanism/humanist-core/actions/workflows/tests.yml/badge.svg)

**Version:** 0.5.0-alpha  
**License:** AGPLv3  
**Based on:** [The Digital Humanism Manifesto](https://github.com/digital-humanism/manifesto)

## Project Goal

Implementation of "Digital Humanism" protocols into LLM frameworks to protect human agency. The SDK prevents autonomous Machine-to-Machine (M2M) loops, protects against cognitive manipulation, and restores the human right to final semantic decision-making.

## Architecture (Status: v0.2.0-alpha)

## Independent Reviews

- [Digital Humanism as a Commercial Circuit-Breaker and ROI Driver](docs/REVIEW_en.md) — independent AI agent review with a reproducible experiment protocol.

### 1. `safe_harbor.py` (Cryptographic Safe Harbor)

*Implements Principles 3 and 4 of the Manifesto.*

- **SafeHarborLedger**: Local hash-chain for intent logging. Protects against retroactive tampering.
- **SovereigntyManager**: Consent management and simulation of the "Right to be Forgotten".
- **Status:** ✅ Core logic implemented.

### 2. `loop_breaker.py` (Agency Guard)

*Implements Principle 7.1 (Semantic Checkpoints).*

- **CognitiveLoadAnalyzer**: Biometrics of consciousness. Calculates the minimum time required for a biological human to analyze text.
- **AgencyGuardV2**: Detector for M2M loops and anomalous cognitive velocity.
- **DigitalBlockAnalyzer**: Structural entropy detector (embedding-based).
- **Status:** ✅ Cognitive load logic implemented. ✅ Embedding-based vector analyzer implemented.

### 3. `integrations/langchain_guard.py` (Immune System)

- **AgencyGuardCallback**: Integration into LangChain via Callbacks. Monitors autonomous agent hops.
- **Status:** ✅ Conceptual integration implemented.

### 4. `authority.py` (HACP Phase 1 — Authority Core)

*Implements the Authority Core of Architecture v2.0.*

- **IntentEnvelope**: bounded capability space granted by a human.
- **ScopeGuard**: deny-by-default evaluation of proposed actions.
- **DecisionToken**: bounded, expiring human approval — no global flags.
- **Status:** ✅ Phase 1 implemented and tested (invariants 1, 3, 4).

### 5. `boundary.py` (HACP Phase 2 — Boundary Detection)

*Implements risk-weighted autonomy and semantic change detection.*

- **SemanticDeltaGuard**: detects meaningful boundaries (read→write, internal→external, reversible→irreversible)
- **RiskEngine**: context-sensitive risk evaluation across multiple dimensions (irreversibility, externality, privacy, privilege, legal, uncertainty, blast_radius)
- **AutonomyBudget**: cumulative risk budgeting replacing fixed hop counting
- **Status:** ✅ Phase 2 implemented and tested (invariants 2, 5, 7).

### 6. `provenance.py` (HACP Phase 3 — Cryptographic Provenance)

*Causal explainability for consequential actions.*

- **ProvenanceEvent**: immutable graph node with causal parents, payload and policy digests, and a cryptographic signature.
- **EventSigner**: HMAC-SHA256 binding (reference implementation; Ed25519 recommended for production).
- **PolicyDigest**: binds events to the governing policy version — policy change produces a new digest.
- **ProvenanceGraph**: append-only, tamper-detecting graph with `explain()` reconstructing why a consequential action was allowed.
- **Status:** ✅ Phase 3 implemented and tested (Invariant 5).

### 7. `integrations/langchain_v2.py` (HACP Phase 4 — Runtime Integration)

*Production-ready adapter for LangChain agent workflows.*

- **HumanistCallback**: Drop-in callback that enforces HACP protocol
- **Automatic intent registration**: Records human intent in provenance graph at workflow start
- **Tool call evaluation**: Each tool call evaluated through AgencyKernel + RiskEngine
- **Autonomy budget tracking**: Raises `AutonomousLoopDetected` when budget exhausted
- **Semantic boundary detection**: Raises `SemanticBoundaryDetected` on meaningful changes
- **Provenance recording**: All events recorded in causal ProvenanceGraph
- **Status:** ✅ Phase 4 implemented for LangChain.

## Phase 5: Evaluation (v0.5.0)

Comprehensive evaluation framework for measuring HACP v2.0 effectiveness:

### Metrics

- **Runtime Overhead**: Per-envelope latency with P50/P95/P99 percentiles and 95% confidence intervals
- **False Positive Rate**: Percentage of legitimate actions incorrectly blocked
- **Missed Boundary Rate**: Percentage of violations the system failed to detect
- **Approval Fatigue**: Per-session approval counts with temporal trend analysis
- **Per-Phase Detection**: Detection rate and FPR for each HACP phase

### Benchmark Framework

```python
from humanist_core.evaluation import (
    BenchmarkDataset,
    ApprovalFatigueSimulator,
    measure_runtime_overhead_detailed,
    generate_evaluation_report,
)

# Generate synthetic test data
dataset = BenchmarkDataset.generate_balanced_dataset(
    size=1000,
    violation_rate=0.10,
    approval_rate=0.20,
)

# Measure runtime overhead
processor = MockEnvelopeProcessor()
runtime_metrics = measure_runtime_overhead_detailed(processor, dataset.envelopes[:100])

# Simulate approval fatigue
sessions = ApprovalFatigueSimulator.simulate_sessions(num_sessions=100)

# Generate full evaluation report
report = generate_evaluation_report(evaluation_metrics)
```

### Example Report Output

```text
======================================================================
HACP v2.0 EVALUATION REPORT
Generated: 2026-08-10T23:50:24.180178
======================================================================

RUNTIME OVERHEAD
----------------------------------------------------------------------
Mean: 6.39 ms
Median (P50): 6.40 ms
P95: 6.80 ms
P99: 6.98 ms
Std Dev: 0.26 ms
95% CI: [6.34, 6.44] ms

ACCURACY METRICS
----------------------------------------------------------------------
False Positive Rate: 2.07%
Missed Boundary Rate: 10.00%

APPROVAL FATIGUE
----------------------------------------------------------------------
Total Sessions: 100
Total Approvals: 1385
Avg per Session: 13.85
Trend: +0.09 approvals/session

PHASE BREAKDOWN
----------------------------------------------------------------------
Phase 1: 95.00% detection, 2.22% FPR
Phase 2: 90.00% detection, 3.00% FPR
Phase 3: 85.00% detection, 1.00% FPR

======================================================================

```
**Run the full demo:** python examples/evaluation_demo.py


**Target architecture (v2.0 / HACP):** [docs/ARCHITECTURE_v2.0.md](docs/ARCHITECTURE_v2.0.md) — reference implementation pending (milestone v0.2.0).

## ROI Calculator

Enterprise sales demo tool for quantifying the financial impact of HACP deployment.

```bash
python examples/roi_calculator.py
```

Pricing model: perpetual license (CAPEX) + annual support (15% of license, OPEX, CPI+1.5% uplift from Y2). The license is priced so the client hits a target ROI on capital (--target-roi, default 12%, working band 10-15%). Capacity Unit: 50K transactions/day / 9.1 reviewer FTE / 13.85 approvals per session; exceeding any dimension adds a unit.
ULA negotiated separately (2-3 yr term, certification at term end).
The report includes baseline risk exposure, prevented incidents, false-positive review costs, payback, breakeven incident rate, 3-year TCO, and validation warnings for unrealistic assumptions.

## Test Coverage

**Test suite:** 122 tests, 100% coverage (816 statements, 0 missed)

- Phase 1 (Authority Core): invariants 1, 3, 4
- Phase 2 (Boundary Detection): invariants 2, 5, 7
- Phase 3 (Cryptographic Provenance): invariant 5
- Phase 4 (Runtime Integration): LangChain adapter edge cases
- Phase 5 (Evaluation): synthetic benchmarks and metrics
- Phase 5.1 (Coverage Hardening): all uncovered branches closed

Run tests:
```bash
pytest tests/ --cov=humanist_core --cov-report=term-missing
```

## Quick Start

```bash
pip install -r requirements.txt
```