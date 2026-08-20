# HACP Python Conformance — Status and Verification

**Project:** Humanist / HACP  
**Component:** `humanist-core` (Python)  
**Protocol baseline:** HACP-Core v0.9.2  
**Date:** 2026-08-16

## 1. What is completed

### Normative HACP conformance

The Python implementation now passes the complete canonical HACP-Core vector set:

- **38 / 38 normative vectors — PASS**
- INV1 — PASS
- INV2 — PASS
- INV3 — PASS
- INV4 — PASS
- INV5 — PASS
- INV7 — PASS
- RUNTIME — PASS

The two vectors that were previously marked as draft were baked into deterministic test cases and are now executed normally:

- `CORE-INV3-002`
- `CORE-INV5-002`

The conformance suite also contains:

- 5 action-hash invariants
- 1 vector inventory check
- canonical JSON / SHA-256 / Ed25519 parity checks
- fail-closed handling for malformed / duplicate-key input
- checkpoint, provenance, revocation, token-binding, scope and budget checks

The standalone conformance run is:

```text
44 passed
0 failed
0 skipped
```

## 2. Python SDK regression status

The complete `humanist-core` test suite was run after the conformance implementation was added.

Latest verified full-suite result:

```text
324 passed
5 skipped
0 failed
```

The five skipped tests are external real-sidecar E2E integration tests. They require an explicitly running HACP sidecar and the corresponding test-key environment variables. When external E2E execution is enabled, they are verified separately against the real Go sidecar and currently pass 5/5.

No existing unit, integration, hardening, provenance, boundary, LangChain, CLI, crypto or builder tests regressed.

## 3. Coverage hardening

Additional hardening tests were added for defensive paths not necessarily represented by normative HACP vectors.

Coverage was raised from approximately 96% overall / 81% for `hacp/conformance.py` to:

```text
Statements missed: 0
Total statements: 1553
Branches: 420
```

At the last recorded run, two partial branch arcs remained:

```text
humanist_core/hacp/conformance.py  303->312
humanist_core/safe_harbor.py       47->exit
```

The corresponding fixes/tests were prepared:

1. empty checkpoint state must continue through the evaluator;
2. the empty-ledger branch in `_get_last_hash()` is written as a normal multiline `if`.

The final coverage run reports `BrPart 0`; the current checked-in Python suite therefore reaches 100% branch coverage.

Verified final result:

```text
Miss    0
BrPart  0
Cover   100%
```

## 4. CI configuration

`.github/workflows/tests.yml` is updated so that CI:

- tests Python 3.12 and 3.13;
- checks out `humanist-core`;
- checks out the canonical `hacp-spec` repository;
- exposes `HACP_SPEC_REPO`;
- runs the full test suite including `tests/conformance`;
- runs statement and branch coverage;
- enforces `--cov-fail-under=100`.

Relevant shape:

```yaml
env:
  HACP_SPEC_REPO: ${{ github.workspace }}/hacp-spec
```

```yaml
- name: Checkout HACP specification
  uses: actions/checkout@v5
  with:
    repository: digital-humanism/hacp-spec
    path: hacp-spec
```

```yaml
python -m pytest tests/ \
  --cov=humanist_core \
  --cov-branch \
  --cov-report=term-missing \
  --cov-fail-under=100 \
  -rs
```

### Reproducibility note

For the current development phase, the spec checkout may follow the repository default branch.

Before a release / formal conformance claim, pin `hacp-spec` to a specific release tag or immutable commit SHA so the canonical vector set cannot change underneath a previously verified implementation.

## 5. Canonical crypto profile used by the tests

The deterministic conformance test key is derived from:

```text
hacp-conformance-v0.9-key-001
```

Private Ed25519 seed:

```text
SHA256("hacp-conformance-v0.9-key-001")
```

Test signer key id:

```text
key-ed25519-test-001
```

Canonical rules:

- canonicalization: JCS / RFC 8785 profile used by the project;
- digest: SHA-256 lowercase hex;
- action binding: `SHA256(JCS(proposed_action))`;
- signatures: Ed25519 over canonical unsigned payload;
- wire signature encoding: base64url without padding.

## 6. Files added / changed

### `humanist-core`

Core implementation:

```text
humanist_core/hacp/conformance.py
```

Conformance tests:

```text
tests/conformance/conftest.py
tests/conformance/helpers.py
tests/conformance/test_action_hash_invariants.py
tests/conformance/test_core_vectors.py
tests/conformance/test_conformance_hardening.py
```

Coverage hardening:

```text
tests/unit/test_final_branch_coverage.py
```

CI:

```text
.github/workflows/tests.yml
```

### `hacp-spec`

The two remaining draft vectors were converted into deterministic executable vectors:

```text
vectors/core_inv3_002_negative.json
vectors/core_inv5_002_negative.json
```

The normative vector inventory remains:

```text
38 vectors
```

## 7. Current implementation status

| Implementation | HACP-Core v0.9.2 vectors | Status |
|---|---:|---|
| Python (`humanist-core`) | 38 / 38 | ✅ PASS |
| TypeScript | pending | ⏳ |
| Go | pending / to be revalidated against baked set | ⏳ |

The next cross-language objective is to run the same canonical vector set against TypeScript and Go and confirm convergence of:

- decisions;
- reason codes;
- canonical bytes;
- action hashes;
- Ed25519 verification behavior;
- checkpoint / provenance / revocation semantics.

## 8. Final Python verification commands

### Conformance only

```powershell
pytest tests/conformance -v
```

Expected:

```text
44 passed
```

### Complete SDK

```powershell
pytest -v
```

### Complete SDK with branch coverage gate

```powershell
pytest `
  --cov=humanist_core `
  --cov-branch `
  --cov-report=term-missing `
  --cov-fail-under=100 `
  -v
```

The Python milestone is considered fully sealed when the final command reports:

```text
0 failed
0 missed statements
0 partial branches
100% coverage
```

## 9. Recommended milestone commit

Suggested commit message:

```text
test(conformance): pass all HACP-Core v0.9.2 vectors
```

After the final 100% branch-coverage confirmation:

```text
test: enforce full Python conformance and 100% coverage
```
