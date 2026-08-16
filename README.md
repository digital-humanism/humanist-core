**# humanist-core SDK**

![tests](https://github.com/digital-humanism/humanist-core/actions/workflows/tests.yml/badge.svg)

****Version:**** 0.5.0-alpha  
****License:**** AGPL-3.0-or-later  
****Architecture:**** Human Agency Continuity Protocol (HACP) v2.0  
****Current wire interoperability:**** HACP v0.9  
****Based on:**** [The Digital Humanism Manifesto](https://github.com/digital-humanism/manifesto)

**## Project Goal**

`humanist-core` is an SDK for implementing Digital Humanism protocols in LLM and autonomous-agent frameworks.

The project focuses on preserving ****human agency as a continuity property of autonomous execution****: an autonomous system may act within explicitly granted authority, but must not silently cross meaningful semantic, scope, risk, or externality boundaries.

The current implementation combines:

- bounded human authority through `IntentEnvelope` and `DecisionToken`;
- semantic boundary detection;
- risk-weighted autonomy budgets;
- causal provenance;
- LangChain runtime integration;
- HACP wire-level interoperability with the Go `hacp-sidecar`;
- evaluation and benchmarking tools.

**## Architecture Status**

The repository contains both the original experimental prototype and the current HACP architecture.

| Area | Status |
|---|---|
| Legacy prototype mechanisms | Implemented and retained for research/history |
| HACP Phase 1 — Authority Core | ✅ Implemented and tested |
| HACP Phase 2 — Boundary Detection | ✅ Implemented and tested |
| HACP Phase 3 — Cryptographic Provenance | ✅ Implemented and tested |
| HACP Phase 4 — LangChain Runtime Integration | ✅ Implemented and tested |
| HACP Phase 5 — Evaluation Framework | ✅ Implemented and tested |
| Python HACP SDK | ✅ Implemented |
| Python HACP SDK conformance | ✅ HACP-Core v0.9.2 — 38/38 normative vectors PASS |
| Python SDK full regression suite | ✅ 318 passed / 5 external-sidecar tests skipped / 0 failed |
| Python ↔ Go sidecar wire interoperability | ✅ Verified |
| Signed `IntentEnvelope` + `DecisionToken` → real sidecar `ALLOW` | ✅ Verified |
| Full HACP v2.0 reference implementation | 🚧 In progress |
| Humanist Core 2.0 production hardening roadmap | 📋 Defined |

The current architectural target is documented in [`docs/ARCHITECTURE_v2.0.md`](docs/ARCHITECTURE_v2.0.md).

The original prototype architecture is retained as historical context in `docs/ARCHITECTURE_v0.1.md`.

**## HACP Sidecar Integration**

`humanist-core` now includes a Python HACP SDK under:

```text
humanist_core/hacp/
```

The verified request path is:

```text
Application
    ↓
humanist-core HACP SDK
    ↓
IntentEnvelope + DecisionToken
    ↓
JCS + Ed25519 + SHA-256 + Base64url
    ↓
X-HACP-Intent-Envelope
X-HACP-Decision-Token
    ↓
hacp-sidecar (Go)
    ↓
schema / signatures / binding / scope / budget / provenance
    ↓
ALLOW / DENY / CHECKPOINT
```

The E2E integration verifies:

- fail-closed behavior without HACP credentials;
- HACP v0.9 wire compatibility;
- JCS compatibility between Python and Go;
- Ed25519 interoperability;
- HTTP `ProposedAction` / `action_hash` compatibility;
- signed envelope/token binding;
- real sidecar `ALLOW`;
- public `SidecarClient` → real sidecar `ALLOW`;
- `max_uses` enforcement and replay protection.

See:

- [`docs/Integration with HACP Sidecar.md`](docs/Integration%20with%20HACP%20Sidecar.md)
- [`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md)
- [`docs/README.md`](docs/README.md)

For the current Python SDK verification baseline, normative conformance status, negative-path coverage, and assurance limitations, see:

- [`docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md`](docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md) — current HACP-Core v0.9.2 Python conformance status and reproducible verification record;
- [`docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md)

**## Roadmap**

Humanist Core is currently in the ****model validation**** stage.

The current focus is on validating the HACP authority model, Action Boundaries, Semantic Checkpoints, Autonomy Budgets, and cross-language interoperability before freezing the protocol surface for production use.

The planned ****Humanist Core 2.0**** milestone is focused on technological completion rather than expansion of scope. Its purpose is to close the production and protocol-hardening gaps around the current model, including:

- human-governed authority roots and authority lineage;
- mandatory attenuation for delegated authority;
- provenance-aware M2M loop breaking;
- full Semantic Checkpoint and reauthorization flows;
- typed action semantics and MCP-native enforcement;
- key lifecycle, rotation, and revocation;
- normative conformance as a release gate;
- negative E2E security coverage, property testing, and fuzzing;
- protocol versioning and compatibility rules;
- anti-bypass production deployment requirements;
- privacy-minimized provenance and observability;
- a formal threat model.

The project intentionally keeps HACP focused on ****Agency Management and action-boundary enforcement****, rather than turning it into a content-moderation system, IAM replacement, service mesh, SIEM, or universal policy engine.

See:

- [`docs/HUMANIST_CORE_2.0_ROADMAP.md`](docs/HUMANIST_CORE_2.0_ROADMAP.md) — Humanist Core 2.0 technology-completion roadmap

**## Core Components**

**### `authority.py` — HACP Authority Core**

Provides bounded authorization primitives.

- `IntentEnvelope`
- `ScopeGuard`
- `DecisionToken`
- deny-by-default scope evaluation

****Status:**** ✅ Implemented and tested.

**### `boundary.py` — Semantic Boundary and Risk Engine**

Provides risk-weighted autonomy and semantic change detection.

- `SemanticDeltaGuard`
- `RiskEngine`
- `AutonomyBudget`
- read → write boundary detection
- internal → external boundary detection
- reversible → irreversible boundary detection

****Status:**** ✅ Implemented and tested.

**### `provenance.py` — Causal Provenance**

Provides causal explainability for consequential actions.

- immutable provenance events;
- causal parent relationships;
- policy digests;
- tamper detection;
- `explain()` reconstruction.

****Status:**** ✅ Implemented and tested.

**### `integrations/langchain_v2.py` — Runtime Integration**

Provides a LangChain callback adapter that applies HACP controls to agent workflows.

- automatic intent registration;
- tool-call evaluation;
- autonomy-budget tracking;
- semantic-boundary enforcement;
- causal provenance recording.

****Status:**** ✅ Implemented and tested.

**### `humanist_core/hacp/` — HACP Python SDK**

Provides the wire-facing Python implementation used with `hacp-sidecar`.

Key modules:

```text
models.py       HACP wire/data models
builders.py     EnvelopeBuilder / TokenBuilder
crypto.py       JCS / Ed25519 / SHA-256 / Base64url
client.py       SidecarClient
exceptions.py   typed HACP reason-code mapping
cli.py          command-line interface
conformance.py  clean-room HACP-Core v0.9.2 conformance evaluator
```

The Python conformance evaluator is intentionally wire-dictionary based and separate from the SDK dataclass API. It is used for differential verification against the canonical `hacp-spec` vectors and currently passes the full **38/38 HACP-Core v0.9.2 normative vector set**.

See [`docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md`](docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md) for the current verification record.

**### `safe_harbor.py` and `loop_breaker.py` — Prototype / Research Components**

These components preserve earlier project research into tamper-evident intent logging, loop detection, cognitive-load heuristics, and digital-block similarity.

They remain useful as experimental mechanisms and historical context, but the current HACP v2.0 architecture does ****not**** define biological-human detection as its central trust primitive.

For the current trust model, see [`docs/ARCHITECTURE_v2.0.md`](docs/ARCHITECTURE_v2.0.md).

**## Evaluation Framework**

The repository includes an evaluation framework for measuring:

- runtime overhead;
- false-positive rate;
- missed-boundary rate;
- approval fatigue;
- per-phase detection behavior.

Example:

```python
from humanist_core.evaluation import (
    BenchmarkDataset,
    ApprovalFatigueSimulator,
    measure_runtime_overhead_detailed,
    generate_evaluation_report,
)
```

Run the demo:

```bash
python examples/evaluation_demo.py
```

**## ROI Calculator**

The repository also includes an enterprise ROI modeling tool:

```bash
python examples/roi_calculator.py
```

The calculator models risk exposure, false-positive review cost, payback, breakeven incident rate, and multi-year TCO.

Its outputs should be interpreted as scenario/model results rather than universal empirical performance claims.

**## Test and Verification Baseline

Current validated Python baseline:

```text
HACP-Core v0.9.2 normative vectors:   38 / 38 PASS
Conformance test suite:               44 passed
Full collected test suite:            323 tests
Passed:                               318
External sidecar E2E skipped:           5
Failed:                                 0
Warnings:                               0
Missed statements:                      0
```

The five skipped tests belong to the real external `hacp-sidecar` E2E layer. They require a running Go sidecar and configured local test signing identity. They are intentionally skipped when the external E2E environment is not enabled.

### Normative HACP conformance

`humanist-core` now executes the complete HACP-Core v0.9.2 canonical vector set from `hacp-spec`.

Verified result:

```text
38 / 38 normative HACP-Core vectors PASS
0 failed
0 skipped
```

The conformance layer covers:

- principal and authority invariants;
- semantic boundary enforcement;
- `DecisionToken` / `IntentEnvelope` binding;
- causal provenance;
- Ed25519 / JCS / SHA-256 interoperability;
- key, envelope, and token revocation;
- autonomy-budget enforcement;
- checkpoint/runtime behavior;
- fail-closed handling for malformed and duplicate-key inputs.

The conformance suite additionally verifies five `action_hash` invariants and the canonical 38-vector inventory:

```text
44 passed
```

The canonical action binding is:

```text
action_hash = SHA256(JCS(proposed_action))
```

Detailed status and reproducibility notes are maintained in:

- [`docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md`](docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md)

### Coverage status

All checked-in Python statements are currently exercised (`0` missed statements). Branch hardening is also enforced in the CI configuration through `--cov-branch`.

The latest recorded local run has two remaining partial branch arcs, so **100% branch coverage must not be claimed until the final coverage run reports `BrPart 0`**.

This result is treated as a **regression and reproducibility baseline, not as a security proof**.

Run the normative conformance suite:

```bash
pytest tests/conformance -v
```

Reference result:

```text
44 passed
```

Run the complete suite:

```bash
pytest -v
```

Run the complete coverage gate:

```bash
pytest \
  --cov=humanist_core \
  --cov-branch \
  --cov-report=term-missing \
  --cov-fail-under=100 \
  -v
```

The CI workflow also checks out the canonical `hacp-spec` repository and exposes it through:

```text
HACP_SPEC_REPO
```

For release-grade reproducibility, the `hacp-spec` checkout should be pinned to a specific release tag or immutable commit SHA.

Run the external HACP sidecar E2E suite:

```bash
pytest tests/test_hacp_sidecar_integration.py -vv -rs --tb=long
```

The E2E suite requires a running sidecar and shared local test identity.

See:

- [`docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md`](docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md) — HACP-Core v0.9.2 Python conformance status;
- [`docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md) — detailed verification and security-hardening record;
- [`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md) — operational external-sidecar verification procedure.

## Quick Start**

Create and activate a virtual environment, then install the project:

```bash
pip install -e .
```

Verify the CLI:

```bash
humanist --help
```

Basic SDK imports:

```python
from humanist_core.hacp import (
    EnvelopeBuilder,
    TokenBuilder,
    SidecarClient,
)
```

For real sidecar integration, follow:

[`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md)

**## Documentation**

Start with [`docs/README.md`](docs/README.md).

Key documents:

- [`docs/ARCHITECTURE_v2.0.md`](docs/ARCHITECTURE_v2.0.md) — current HACP architecture;
- [`docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md`](docs/conformance/HACP_PYTHON_CONFORMANCE_STATUS.md) — current Python HACP-Core v0.9.2 conformance status, 38/38 vector baseline, CI and coverage verification;
- [`docs/HUMANIST_CORE_2.0_ROADMAP.md`](docs/HUMANIST_CORE_2.0_ROADMAP.md) — roadmap from model validation to production-grade Humanist Core 2.0;
- [`docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md) — reproducible Python SDK verification baseline, security hardening, negative-path testing, coverage methodology, and assurance limitations;
- [`docs/Integration with HACP Sidecar.md`](docs/Integration%20with%20HACP%20Sidecar.md) — implementation and interoperability record;
- [`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md) — operational verification procedure;
- [`docs/REVIEW_en.md`](docs/REVIEW_en.md) — independent review;
- `docs/ARCHITECTURE_v0.1.md` — legacy prototype architecture after migration.

**## Contributing**

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

Changes to HACP wire models, canonicalization, signatures, action binding, or sidecar interaction should include corresponding unit and/or E2E verification.

Security-relevant changes should test both the expected path and applicable fail-closed / negative paths.

The established Python statement- and branch-coverage gates should not be reduced without an explicit documented reason.

Do not add artificial tests that mutate private implementation state solely to satisfy coverage metrics; prefer public-API verification or removal of unreachable/duplicated logic.

**## License**

This project is licensed under the GNU Affero General Public License v3.0 or later. See [`LICENSE`](LICENSE).

Commercial licensing information is available in [`COMMERCIAL.md`](COMMERCIAL.md).

**---**

****Contact:**** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)