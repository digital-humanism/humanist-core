# Contributing to humanist-core

Thank you for considering contributing to `humanist-core`.

The project combines research prototypes, HACP protocol components, runtime integrations, cryptographic wire behavior, and evaluation tooling. Changes should preserve both implementation correctness and protocol interoperability.

## Before You Start

Please read:

1. [The Digital Humanism Manifesto](https://github.com/digital-humanism/manifesto)
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) — architecture entry point
3. [`docs/ARCHITECTURE_v2.0.md`](docs/ARCHITECTURE_v2.0.md) — current HACP architecture
4. [`docs/README.md`](docs/README.md) — documentation index and current project status

For HACP wire, SDK, or sidecar changes, also read:

- [`docs/Integration with HACP Sidecar.md`](docs/Integration%20with%20HACP%20Sidecar.md)
- [`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md)
- [`docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md)

For significant architectural or protocol changes, open an issue before implementation.

## Development Setup

Install the project in editable mode:

```bash
pip install -e .
```

Run the complete test suite:

```bash
pytest tests/
```

For coverage:

```bash
pytest tests/ --cov=humanist_core --cov-report=term-missing
```

## Pull Request Process

1. Fork the repository.
2. Create a focused feature branch.
3. Keep changes scoped and reviewable.
4. Write code, comments, docstrings, and public documentation in English.
5. Follow the existing project style.
6. Add or update tests for changed behavior.
7. Add negative-path and fail-closed tests for security-relevant behavior where applicable.
8. Update documentation when a public contract, architecture, CLI, wire model, or operational procedure changes.
9. Run the relevant verification gates before submitting.
10. Submit a pull request with a clear description of behavior, compatibility impact, and validation results.

A pull request that changes security-relevant HACP behavior should explain:

- what authority or protocol behavior changed;
- whether wire compatibility is affected;
- what negative or fail-closed cases were tested;
- whether Python ↔ Go interoperability was re-verified;
- whether the established coverage baseline remains intact.

## Verification Gates

### General Changes

Run:

```bash
pytest tests/
```

Current default local baseline:

```text
Collected tests:                     216
Passed:                              211
External-sidecar E2E skipped:          5
Warnings:                              0
```

The five skipped tests belong to the real external `hacp-sidecar` E2E layer and are expected to be skipped when the external environment is not enabled.

### HACP SDK Changes

For changes under `humanist_core/hacp/`, run the HACP unit suite:

```bash
pytest tests/unit/ -vv --tb=short
```

The HACP SDK test set includes:

- builder tests;
- builder security-hardening tests;
- client tests;
- CLI tests;
- crypto tests;
- crypto hardening tests;
- JCS canonicalization tests;
- final branch/edge-path coverage tests.

Security-relevant HACP changes should test both the expected path and applicable negative paths.

Examples include:

- missing or invalid authority;
- malformed scope;
- missing action binding;
- invalid decision values;
- malformed cryptographic input;
- missing HACP decision headers;
- unknown HACP decisions;
- invalid CLI transport parameters.

### HACP Wire / Sidecar Changes

Changes affecting any of the following require E2E verification:

- `IntentEnvelope`;
- `DecisionToken`;
- `Scope`;
- constraints;
- JCS canonicalization;
- Ed25519 handling;
- Base64url encoding;
- HTTP `ProposedAction`;
- `action_hash`;
- HACP headers;
- `SidecarClient`;
- token budget/replay behavior.

Run:

```bash
pytest tests/test_hacp_sidecar_integration.py -vv -rs --tb=long
```

Current external E2E baseline:

```text
5 passed
```

when the required external sidecar environment is enabled.

Follow the environment setup in:

[`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md)

### Coverage

Run:

```bash
pytest tests/ --cov=humanist_core --cov-report=term-missing
```

Current validated Python baseline:

```text
Statements:                         1336
Missed statements:                     0
Statement coverage:                  100%
Warnings:                              0
```

The current Python implementation therefore has **100% statement coverage** for the checked-in test suite.

This is a **regression and reproducibility baseline, not a security proof**.

A change should not reduce the established statement-coverage baseline without an explicit and documented reason.

Do not add tests that mutate private implementation state solely to satisfy coverage metrics. Prefer:

- testing through the public API;
- adding meaningful negative-path tests;
- simplifying duplicated or unreachable implementation logic.

Detailed verification methodology is documented in:

[`docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md`](docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md)

## Security-Relevant Testing Principles

Security-relevant changes should be tested according to behavior, not only line execution.

Where applicable, include both:

```text
expected valid path
```

and:

```text
invalid / incomplete / adversarial path
```

Examples:

```text
valid authority                 → ALLOW
missing authority               → DENY
invalid signature               → DENY
wrong action binding            → DENY
missing scope dimension         → fail closed
unknown sidecar decision        → fail closed
expired authority               → DENY
budget exhaustion               → DENY / CHECKPOINT
replay                          → DENY
semantic boundary crossing      → CHECKPOINT / REAUTHORIZE
```

Do not weaken fail-closed behavior in order to preserve backward compatibility.

If compatibility and fail-closed behavior conflict, document the issue and open a design discussion before changing the protocol behavior.

## HACP Compatibility Rules

HACP is a cross-language wire protocol. Local Python tests alone are not sufficient for wire-facing changes.

A passing:

```text
Python sign → Python verify
```

does not prove:

```text
Python sign → Go verify
```

When changing wire behavior:

- preserve canonical field names and types;
- treat array/scalar representation as protocol-significant;
- treat optional-field emission as protocol-significant;
- calculate signatures over canonical bytes;
- preserve `DecisionToken` → `ProposedAction` binding;
- preserve action-specific `action_hash` semantics;
- preserve explicit fail-closed behavior;
- use real sidecar E2E tests when interoperability may be affected.

Any change to canonicalization, wire serialization, signatures, action binding, or HACP headers should be treated as potentially cross-language breaking until verified.

## Test Design Guidance

Tests should preferably verify externally observable behavior.

Prefer:

```python
builder.build_unsigned()
client.request(...)
signed_token.to_b64url()
```

over direct mutation of private fields.

Avoid tests such as:

```python
builder._expires_at = None
```

when their only purpose is to execute otherwise unreachable code.

If a branch is unreachable through the public API, first determine whether the branch represents:

- intentionally defensive code;
- duplicate initialization;
- stale implementation logic;
- a missing public scenario.

Simplify implementation logic when appropriate rather than creating artificial coverage.

## Generated and Local Artifacts

Do not commit local/generated artifacts such as:

```text
.coverage
htmlcov/
.pytest_cache/
__pycache__/
*.pyc
*.egg-info/
*.log
*.jsonl
```

Do not commit local private keys or developer-specific test key files.

The deterministic conformance identity may be generated locally as documented in the HACP verification guide.

Private key material must never be committed.

## Documentation

Documentation should avoid machine-specific absolute paths.

Prefer:

```text
...\GitHub\Dev\humanist-core
...\GitHub\Dev\hacp-sidecar
```

over developer-specific paths such as:

```text
...\GitHub\Dev\humanist-core
```

or other workstation-specific repository roots.

When commands are platform-specific, state the shell/platform explicitly.

Public documentation should clearly distinguish between:

```text
Humanist Core package version
HACP architecture target
current HACP wire version
current implementation state
future production-hardening milestones
```

Current terminology:

```text
humanist-core package:        0.5.0-alpha
architecture target:          HACP v2.0
current wire interoperability: HACP v0.9
development stage:            Model Validation
```

Do not describe the full HACP v2.0 architecture as implemented unless the corresponding roadmap gates have actually been completed.

## Documentation Updates Required by Change Type

Update the relevant documentation when changing:

| Change | Documentation |
|---|---|
| Architecture or authority model | `docs/ARCHITECTURE_v2.0.md` |
| 2.0 scope / release gates | `docs/HUMANIST_CORE_2.0_ROADMAP.md` |
| Python ↔ Go integration | `docs/Integration with HACP Sidecar.md` |
| E2E setup or commands | `docs/HACP Integration Verification Guide.md` |
| Verification methodology / baseline | `docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md` |
| New documentation file | `docs/README.md` |
| Public project status | root `README.md` |

## Assurance Philosophy

Humanist Core should make claims that users and reviewers can independently reproduce.

Prefer:

> The current Python implementation reaches 100% statement coverage for the checked-in test suite and is supplemented by explicit negative-path tests and separate real Python ↔ Go sidecar E2E verification.

Avoid:

> HACP is secure because coverage is 100%.

Coverage is one assurance layer.

Future and complementary assurance layers include:

- branch coverage;
- mutation testing;
- property-based testing;
- fuzzing;
- differential cross-language conformance;
- expanded negative E2E;
- threat-model-driven testing;
- production anti-bypass verification.

## Contributor License Agreement

By submitting a pull request, you agree to the terms of [`CLA.md`](CLA.md).

Please include the following line in your first pull request description:

> I have read and agree to the Contributor License Agreement.

---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)
