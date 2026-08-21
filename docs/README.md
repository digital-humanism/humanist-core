### Version domains

| Domain | Version |
|---|---|
| Python package | `humanist-core 0.5.0` |
| HACP specification release | `0.9.3` |
| HACP-Core conformance baseline | `0.9.2` |
| Wire protocol family | `0.9` |
| Architecture generation | `v2.0` |

These versions belong to separate domains and MUST NOT be conflated. The `humanist-core` package currently implements and validates against the HACP-Core `0.9.2` canonical baseline, interoperates over the HACP `0.9` wire family, and is released as Python package `0.5.0`. The broader architectural generation remains identified as `v2.0`.

# Humanist Core Documentation

This directory contains the architecture, verification, integration, roadmap, and supporting documentation for `humanist-core` and the Human Agency Continuity Protocol (HACP).

The documentation is intentionally organized around **verifiable implementation state** rather than broad security claims.

Humanist Core is currently in the **model validation** stage. The current Python implementation is mature enough to provide a reproducible verification baseline, while the broader Humanist Core 2.0 production-hardening work remains in progress.

---

## Start Here

If you are new to the project, read these documents in order:

1. [`../README.md`](../README.md)  
   Project overview, architecture status, current verification baseline, and quick start.

2. [`ARCHITECTURE_v2.0.md`](ARCHITECTURE_v2.0.md)  
   Current HACP architecture and the intended authority-continuity model.

3. [`HUMANIST_CORE_2.0_ROADMAP.md`](HUMANIST_CORE_2.0_ROADMAP.md)  
   Roadmap from the current model-validation phase to production-grade Humanist Core 2.0.

4. [`knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md)  
   Detailed and reproducible verification record for the Python HACP SDK.

5. [`Integration with HACP Sidecar.md`](Integration%20with%20HACP%20Sidecar.md)  
   Python ↔ Go sidecar integration and interoperability record.

6. [`HACP Integration Verification Guide.md`](HACP%20Integration%20Verification%20Guide.md)  
   Operational procedure for reproducing the real `hacp-sidecar` E2E verification.

---

## Current Project Status

### Architecture

- **Architecture target:** Human Agency Continuity Protocol (HACP) v2.0
- **Current wire interoperability:** HACP v0.9
- **Current development stage:** Model Validation
- **Humanist Core package version:** 0.5.0

The architecture target and the current wire version are intentionally separate concepts.

HACP v2.0 describes the broader architectural direction, while the currently verified Python ↔ Go wire interoperability is based on HACP v0.9.

### Python verification baseline

The current checked-in Python implementation has the following reference baseline:

```text
Collected tests:                     216
Passed:                              211
External-sidecar E2E skipped:          5
Warnings:                              0
Statements:                         1336
Missed statements:                     0
Statement coverage:                  100%
```

The five skipped tests are environment-dependent real-sidecar E2E tests. They are skipped when the external Go `hacp-sidecar` environment is not enabled.

The 100% statement-coverage result is treated as a **regression and reproducibility baseline, not as a security proof**.

See:

- [`knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md)

---

## Architecture

### Current Architecture

[`ARCHITECTURE_v2.0.md`](ARCHITECTURE_v2.0.md)

Defines the current Humanist/HACP architectural direction, including:

- bounded autonomous authority;
- action-boundary enforcement;
- semantic boundaries;
- autonomy budgets;
- causal provenance;
- cryptographic authority representation;
- verifier-oriented enforcement;
- Semantic Checkpoints;
- authority continuity.

The current architecture should be treated as the primary architectural reference.

### Legacy Architecture

[`ARCHITECTURE_v0.1.md`](ARCHITECTURE_v0.1.md)

Preserves the original experimental architecture for:

- research history;
- comparison;
- provenance of earlier design decisions.

The legacy architecture is **not** the current normative trust model.

---

## Verification and Assurance

### HACP SDK Verification and Test Hardening

[`knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md)

This is the main verification record for the current Python implementation.

It documents:

- the progression to 100% statement coverage;
- security-focused builder tests;
- cryptographic hardening;
- fail-closed behavior;
- action-binding verification;
- SidecarClient negative paths;
- CLI hardening;
- warning cleanup;
- TokenBuilder lifecycle cleanup;
- the meaning and limitations of 100% coverage;
- recommended next assurance layers.

Recommended interpretation:

> 100% statement coverage is a baseline, not a security proof.

The broader assurance model should also include:

- branch coverage;
- mutation testing;
- property-based testing;
- fuzzing;
- differential conformance;
- negative real-sidecar E2E;
- threat-model-driven testing.

---

## HACP Sidecar Integration

### Integration Record

[`Integration with HACP Sidecar.md`](Integration%20with%20HACP%20Sidecar.md)

Describes the implementation and interoperability work between:

```text
humanist-core (Python)
        ↓
IntentEnvelope + DecisionToken
        ↓
JCS / Ed25519 / SHA-256 / Base64url
        ↓
hacp-sidecar (Go)
```

The verified integration includes:

- fail-closed behavior without HACP credentials;
- Python-generated Intent Envelopes;
- Python-generated Decision Tokens;
- Python ↔ Go JCS interoperability;
- Ed25519 signature interoperability;
- HTTP `ProposedAction` / `action_hash` compatibility;
- real sidecar `ALLOW`;
- SidecarClient → real sidecar `ALLOW`;
- `max_uses` enforcement;
- replay protection.

### Verification Procedure

[`HACP Integration Verification Guide.md`](HACP%20Integration%20Verification%20Guide.md)

Provides the operational procedure for running the external E2E environment.

Public documentation should use portable repository paths such as:

```text
...\GitHub\Dev\humanist-core
...\GitHub\Dev\hacp-sidecar
```

Do not publish:

- workstation-specific usernames;
- private user profile paths;
- private key contents;
- local secret material.

---

## Humanist Core 2.0 Roadmap

[`HUMANIST_CORE_2.0_ROADMAP.md`](HUMANIST_CORE_2.0_ROADMAP.md)

Humanist Core 2.0 is a **technology-completion and production-hardening milestone**, not an expansion into general AI content moderation.

The current roadmap includes:

- human-governed authority roots;
- authority lineage;
- mandatory attenuation for delegated authority;
- provenance-aware M2M loop breaking;
- full Semantic Checkpoint and reauthorization flows;
- typed action semantics;
- MCP-native enforcement;
- key lifecycle and revocation;
- protocol versioning;
- conformance as a release gate;
- negative E2E security testing;
- fuzzing and property testing;
- production anti-bypass requirements;
- privacy-minimized provenance;
- formal threat modeling.

The current 100% Python statement-coverage milestone should be considered a completed **verification baseline**, not completion of the entire Humanist Core 2.0 program.

---

## Reviews

### Independent Review

[`REVIEW_en.md`](REVIEW_en.md)

Contains an independent review of the project.

Review documents should be interpreted as external or analytical assessments, not as normative protocol specifications.

---

## Knowledge Base

The `knowledge-base/` directory contains detailed engineering records that are useful for:

- contributors;
- reviewers;
- security analysis;
- reproducibility;
- implementation history.

Current entries:

- [`HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md)  
  Python SDK verification baseline, security hardening, coverage methodology, and assurance limitations.

Future knowledge-base documents may include:

- threat-model records;
- conformance reports;
- protocol compatibility matrices;
- fuzzing and mutation-testing reports;
- release verification records;
- deployment security profiles.

---

## Verification Commands

### Default Python suite

```bash
pytest tests/ --cov=humanist_core --cov-report=term-missing
```

Current reference result:

```text
324 passed
5 external-sidecar E2E tests conditionally skipped
0 failed
100% statement coverage
100% branch coverage (BrPart 0)
external real-sidecar E2E: 5/5 PASS
```

### External Go sidecar E2E

```bash
pytest tests/test_hacp_sidecar_integration.py -vv -rs --tb=long
```

The external E2E suite requires a running `hacp-sidecar` environment and local test signing identity.

---

## Documentation Principles

Humanist/HACP documentation follows several principles.

### 1. Verifiable claims

Security and quality claims should be reproducible where possible.

Prefer:

> The current Python implementation reaches 100% statement coverage for the checked-in suite.

Avoid:

> HACP is secure because coverage is 100%.

### 2. Explicit limitations

Documentation should state what a verification result does and does not prove.

### 3. Fail-closed behavior must be visible

Negative-path tests and failure behavior are part of the public engineering story, not implementation details to hide.

### 4. Architecture and implementation status must remain distinct

The project should distinguish between:

```text
architecture target
current wire version
current implementation state
future production-hardening milestone
```

### 5. Portable paths only

Public documentation should use repository-relative or portable paths.

Use:

```text
...\GitHub\Dev\humanist-core
...\GitHub\Dev\hacp-sidecar
```

Do not use workstation-specific paths.

### 6. No secrets in documentation

Never commit or publish:

- private signing keys;
- PEM contents;
- secret test material;
- local credentials.

---

## Suggested Reading Paths

### For users evaluating the project

```text
README
  ↓
ARCHITECTURE_v2.0
  ↓
HACP SDK Verification and Test Hardening
  ↓
Integration with HACP Sidecar
```

### For contributors

```text
README
  ↓
CONTRIBUTING
  ↓
ARCHITECTURE_v2.0
  ↓
HACP SDK Verification and Test Hardening
  ↓
HACP Integration Verification Guide
```

### For security reviewers

```text
ARCHITECTURE_v2.0
  ↓
HACP SDK Verification and Test Hardening
  ↓
Integration with HACP Sidecar
  ↓
HUMANIST_CORE_2.0_ROADMAP
```

### For implementation maintainers

```text
ARCHITECTURE_v2.0
  ↓
HACP Integration Verification Guide
  ↓
knowledge-base verification records
  ↓
conformance / E2E results
```

---

## Repository Documentation Map

```text
docs/
├── README.md
├── ARCHITECTURE_v2.0.md
├── ARCHITECTURE_v0.1.md
├── HUMANIST_CORE_2.0_ROADMAP.md
├── Integration with HACP Sidecar.md
├── HACP Integration Verification Guide.md
├── REVIEW_en.md
└── knowledge-base/
    └── HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md
```

This map should be updated when new normative, verification, or knowledge-base documents are added.

---

## Contributing to Documentation

When changing architecture, wire behavior, security-relevant implementation, or verification rules:

1. update the implementation;
2. update or add tests;
3. update the relevant technical document;
4. update this documentation index if a new document is added;
5. avoid reducing the established verification baseline without explanation;
6. distinguish implemented behavior from planned behavior;
7. keep public paths and examples machine-independent.

See [`../CONTRIBUTING.md`](../CONTRIBUTING.md) for contributor guidance.

---

## License

Humanist Core is licensed under the GNU Affero General Public License v3.0 or later.

See:

- [`../LICENSE`](../LICENSE)
- [`../COMMERCIAL.md`](../COMMERCIAL.md)

---

## Contact

[Digital Humanism Collective](mailto:digital.humanism.collective@protonmail.com)
