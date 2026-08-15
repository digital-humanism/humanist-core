# Contributing to humanist-core

Thank you for considering contributing to `humanist-core`.

The project combines research prototypes, HACP protocol components, runtime integrations, cryptographic wire behavior, and evaluation tooling. Changes should preserve both implementation correctness and protocol interoperability.

## Before You Start

Please read:

1. [The Digital Humanism Manifesto](https://github.com/digital-humanism/manifesto)
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) — architecture entry point
3. [`docs/ARCHITECTURE_v2.0.md`](docs/ARCHITECTURE_v2.0.md) — current HACP architecture

For HACP wire, SDK, or sidecar changes, also read:

- [`docs/Integration with HACP Sidecar.md`](docs/Integration%20with%20HACP%20Sidecar.md)
- [`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md)

For significant architectural or protocol changes, open an issue before implementation.

## Development Setup

Install the project in editable mode with development dependencies according to the repository's Python environment setup.

Typical local installation:

```bash
pip install -e .
```

Run the complete test suite:

```bash
pytest tests/
```

## Pull Request Process

1. Fork the repository.
2. Create a focused feature branch.
3. Keep changes scoped and reviewable.
4. Write code, comments, docstrings, and public documentation in English.
5. Follow the existing project style.
6. Add or update tests for changed behavior.
7. Update documentation when a public contract, architecture, CLI, wire model, or operational procedure changes.
8. Run the relevant verification gates before submitting.
9. Submit a pull request with a clear description of behavior, compatibility impact, and validation results.

## Verification Gates

### General Changes

Run:

```bash
pytest tests/
```

The current baseline is:

```text
148 passed
```

### HACP SDK Changes

For changes under `humanist_core/hacp/`, run:

```bash
pytest tests/unit/test_builders.py \
       tests/unit/test_client.py \
       tests/unit/test_crypto.py \
       tests/unit/test_jcs.py
```

Current baseline:

```text
21 passed
```

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

Current baseline:

```text
5 passed
```

Follow the environment setup in:

[`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md)

### Coverage

Run:

```bash
pytest tests/ --cov=humanist_core --cov-report=term-missing
```

Current baseline:

```text
Overall project coverage:         91%
Existing internal core coverage: 100%
```

A change should not silently reduce the existing internal core from its 100% coverage baseline.

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
- use real sidecar E2E tests when interoperability may be affected.

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

## Documentation

Documentation should avoid machine-specific absolute paths.

Prefer:

```text
...\GitHub\Dev\humanist-core
```

over a developer-specific path such as:

```text
C:\Users\<name>\...\humanist-core
```

When commands are platform-specific, state the shell/platform explicitly.

## Contributor License Agreement

By submitting a pull request, you agree to the terms of [`CLA.md`](CLA.md).

Please include the following line in your first pull request description:

> I have read and agree to the Contributor License Agreement.
>
> ---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)
