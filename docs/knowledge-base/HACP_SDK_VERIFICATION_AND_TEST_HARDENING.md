# HACP SDK Verification, Security Hardening, and 100% Test Coverage

**Status:** Completed  
**Component:** `humanist-core / humanist_core.hacp`  
**Document role:** Public knowledge-base / verification record  
**Reference test platform:** Windows, Python 3.13.14, pytest 9.1.1  
**Reference result:** `324 passed, 5 external-sidecar E2E tests conditionally skipped, 0 failed`
**Coverage result:** `100% statement coverage, 100% branch coverage (BrPart 0)`
**External real-sidecar E2E:** `5/5 PASS`

---

## 1. Purpose

This document records the verification and test-hardening work performed on the Python HACP SDK in `humanist-core`.

The objective was not to maximize a coverage percentage in isolation. The work focused first on security-significant behavior:

- fail-closed handling;
- authority and action binding;
- signed wire serialization;
- Ed25519 and canonicalization behavior;
- token construction invariants;
- sidecar response handling;
- CLI failure paths;
- HTTP request binding;
- explicit negative tests.

Only after those paths were exercised were the remaining uncovered lines reviewed. Where uncovered code represented duplicated or unreachable logic, the implementation was simplified instead of adding artificial tests against private state.

This distinction matters for a security-oriented control plane: test coverage is useful only when it corresponds to meaningful behavior.

---

## 2. Verification layers

The Humanist/HACP verification model currently uses several layers.

### 2.1. Unit tests

Unit tests validate deterministic behavior of:

- data models;
- builders;
- crypto primitives;
- client behavior;
- CLI behavior;
- canonicalization;
- exception mapping.

### 2.2. Security-hardening tests

Additional tests explicitly target:

- fail-closed behavior;
- invalid and incomplete authority state;
- action hash binding;
- scope dimension failures;
- malformed cryptographic inputs;
- unknown protocol decisions;
- token lifecycle defaults;
- wire round-trips.

### 2.3. Framework integration tests

Existing Humanist Core integration tests continue to validate:

- authority enforcement;
- semantic boundaries;
- autonomy budgets;
- provenance;
- LangChain action-boundary integration;
- loop-breaking behavior.

### 2.4. Real sidecar E2E

A separate external test layer validates Python ↔ Go interoperability against the real `hacp-sidecar`.

These tests are intentionally environment-dependent and are skipped when the external sidecar environment is not enabled.

---

## 3. Baseline progression

Before this hardening phase, the project had:

- 100% coverage for the established internal/core modules;
- a newer HACP SDK with materially lower coverage;
- approximately 91% overall project coverage.

The hardening sequence progressed through:

1. CLI repair and CLI tests;
2. builder security tests;
3. crypto hardening;
4. client negative-path coverage;
5. CLI edge-path coverage;
6. cleanup of duplicate TokenBuilder default initialization.

The final reference run reports:

```text
324 passed
5 external-sidecar E2E tests conditionally skipped
0 failed
100% statement coverage
100% branch coverage (BrPart 0)
external real-sidecar E2E: 5/5 PASS
```

---

## 4. CLI URL handling fix

### Problem

The CLI accepts a complete request URL, for example:

```text
http://127.0.0.1:8080/api/test
```

The earlier implementation passed the entire URL as the `SidecarClient` base URL and then issued a request using an empty relative path.

This could cause HTTP client URL resolution to differ from the endpoint expected by the CLI tests and by the user.

### Resolution

The CLI now separates the complete URL into:

```text
base_url = http://127.0.0.1:8080
path     = /api/test
```

using URL parsing.

Query strings are preserved:

```text
http://127.0.0.1:8080/api/test?limit=10&active=true
```

becomes:

```text
base_url = http://127.0.0.1:8080
path     = /api/test?limit=10&active=true
```

### Security relevance

A transport-addressing bug can make a valid HACP flow appear to fail. Correct endpoint resolution is therefore part of reliable enforcement and diagnosis.

---

## 5. Builder hardening

`builders.py` is security-sensitive because it constructs the structures that are canonicalized, signed, transmitted, and later verified by HACP implementations.

The hardening suite covers the following properties.

### 5.1. Principal is mandatory

An Intent Envelope cannot be built without a principal.

Missing principal state fails closed with a schema validation error.

### 5.2. Scope normalization is deterministic

Boundary dimensions are normalized so scalar input does not accidentally become ambiguous wire semantics.

Relevant dimensions include:

- audiences;
- reversibility;
- externality;
- data classes;
- resource classes;
- verbs.

### 5.3. Protocol and lineage fields are preserved

Tests verify the preservation of fields such as:

- `hacp_version`;
- `principal_kind`;
- `intent_statement`;
- `parent_envelope_id`;
- optional autonomy budget.

This is important for future delegated-authority and authority-lineage work.

### 5.4. Signed Intent Envelope wire round-trip

The signed envelope's Base64url representation is decoded and compared with the signed wire object.

The signature is independently verified over the canonical unsigned payload.

### 5.5. HTTP action synthesis requires authority context

`http_action()` cannot synthesize a token-bound action before an Intent Envelope is attached.

This is enforced as a fail-closed invariant.

### 5.6. HTTP method mapping is deterministic

The SDK verifies deterministic mapping between HTTP methods and HACP action verbs.

Examples:

```text
GET     → read
HEAD    → read
POST    → create
PUT     → update
PATCH   → update
DELETE  → delete
```

The derived verb participates in the action binding.

### 5.7. Payload binding

HTTP request bodies contribute to `payload_hash`.

This means two actions targeting the same path but carrying different bodies do not silently share the same bound semantics.

### 5.8. Explicit action metadata

Tests cover explicit values for:

- resource class;
- audience;
- reversibility;
- externality;
- data class.

This supports typed action semantics and avoids relying exclusively on heuristic inference.

### 5.9. Missing scope dimensions fail closed

HTTP action synthesis rejects empty security dimensions instead of inventing defaults.

Tests cover empty:

- resource classes;
- audiences;
- reversibility;
- externality;
- data classes.

### 5.10. DecisionToken construction

Tests verify:

- envelope requirement;
- proposed-action requirement;
- envelope ID requirement;
- decision validation;
- ALLOW/CHECKPOINT/DENY preservation;
- token ID generation;
- issued/expiry timestamps;
- signer key ID;
- policy digest;
- constraints;
- maximum uses;
- token signature;
- canonical serialization.

---

## 6. TokenBuilder lifecycle cleanup

Coverage analysis revealed duplicated TokenBuilder default initialization.

`expires_at` and `signer_key_id` were being initialized during envelope attachment and then guarded again during final token construction.

Because normal public API usage always attaches an envelope before building a token, the later fallback branches were effectively unreachable.

The project deliberately did **not** add tests that manually corrupted private state such as:

```python
builder._expires_at = None
builder._signer_key_id = None
```

solely to execute those lines.

Instead, TokenBuilder responsibilities were clarified:

- `envelope(...)` attaches the authority envelope;
- `build_unsigned()` performs token default finalization.

This provides a single, clear finalization point while preserving explicit setter precedence.

The result is simpler code and meaningful 100% coverage.

---

## 7. Cryptographic hardening

`crypto.py` now has 100% statement coverage.

The test suite validates:

### 7.1. Ed25519 key generation

Generated keypairs successfully complete an Ed25519 sign/verify round-trip.

### 7.2. Deterministic-seed rejection

The public helper does not pretend to support an unsafe or unsupported deterministic seed-generation interface.

The unsupported path raises an explicit error.

### 7.3. PEM loading

Tests cover:

- PEM bytes;
- PEM string input;
- Ed25519 private keys;
- rejection of RSA/non-Ed25519 private keys.

### 7.4. Raw public key representation

An Ed25519 raw public key is exactly 32 bytes.

### 7.5. Strict input types

Signing and verification helpers reject invalid payload/signature types.

### 7.6. Base64url

Tests cover:

- no-padding encoding;
- bytes input;
- binary edge-value round-trip;
- decoder padding restoration.

### 7.7. Canonicalization compatibility

The SDK normalizes canonicalization output to bytes if the JCS implementation returns a string.

### 7.8. SHA-256 and action hashing

Tests validate:

- known SHA-256 vectors;
- string and byte input;
- canonical object-order independence;
- security-semantic sensitivity.

Changing a security-relevant field such as:

```text
audience: internal
```

to:

```text
audience: external
```

changes the action hash.

---

## 8. SidecarClient hardening

`client.py` now has 100% statement coverage.

Tests verify:

- signed Intent Envelope object injection;
- signed Decision Token object injection;
- raw Base64url credentials;
- `X-HACP-Intent-Envelope`;
- `X-HACP-Decision-Token`;
- `X-HACP-Policy-Context`;
- `X-HACP-Tool-Name`;
- ALLOW;
- CHECKPOINT;
- DENY;
- missing HACP decision header;
- unknown HACP decision;
- network failure;
- context-manager cleanup.

### Fail-closed rule

An unknown decision such as:

```text
X-HACP-Decision: MAGIC
```

is never interpreted as ALLOW.

This is an explicit negative test.

---

## 9. CLI hardening

`cli.py` now has 100% statement coverage.

The suite covers:

- envelope creation to stdout;
- envelope creation to file;
- invalid signing key path;
- envelope options;
- token creation to stdout;
- token creation to file;
- invalid envelope/action paths;
- GET request;
- POST request;
- DENY handling;
- connection failure;
- missing HACP headers;
- invalid absolute URL;
- query-string preservation;
- module entrypoint.

---

## 10. Warning-free entrypoint testing

The initial module-entrypoint test used `runpy.run_module()` after the CLI module had already been imported during pytest collection.

Python 3.13 correctly emitted a runtime warning because the same module was already present in `sys.modules`.

The warning was not globally suppressed.

Instead, the test temporarily removes only the CLI submodule from `sys.modules` before executing it as `__main__`. Pytest's `monkeypatch` restores state after the test.

The final reference suite therefore reports:

```text
0 warnings
```

---

## 11. Final coverage result

Reference command:

```powershell
pytest tests\ --cov=humanist_core --cov-report=term-missing
```

Reference result:

```text
324 passed
5 external-sidecar E2E tests conditionally skipped
0 failed
100% statement coverage
100% branch coverage (BrPart 0)
external real-sidecar E2E: 5/5 PASS
```

Coverage:

```text
Name                                            Cover
-----------------------------------------------------
humanist_core\__init__.py                       100%
humanist_core\authority.py                      100%
humanist_core\boundary.py                       100%
humanist_core\evaluation\__init__.py            100%
humanist_core\evaluation\benchmark.py           100%
humanist_core\evaluation\metrics.py             100%
humanist_core\hacp\__init__.py                  100%
humanist_core\hacp\builders.py                  100%
humanist_core\hacp\cli.py                       100%
humanist_core\hacp\client.py                    100%
humanist_core\hacp\crypto.py                    100%
humanist_core\hacp\exceptions.py                100%
humanist_core\hacp\models.py                    100%
humanist_core\integrations\langchain_guard.py   100%
humanist_core\integrations\langchain_v2.py      100%
humanist_core\loop_breaker.py                   100%
humanist_core\provenance.py                     100%
humanist_core\safe_harbor.py                    100%
-----------------------------------------------------
TOTAL                                           100%
```

Totals:

```text
0 missed statements
100% statement coverage
100% branch coverage (BrPart 0)
```

---

## 12. Why five tests are skipped in the default run

Five tests belong to the external real-sidecar E2E layer.

They require a running Go `hacp-sidecar` and a configured test signing identity.

The skipped tests validate:

- fail-closed behavior without HACP headers;
- Python HTTP action hash compatibility with the Go sidecar;
- Python envelope/token signature consistency;
- real signed Python request accepted by the Go sidecar;
- `SidecarClient` receiving ALLOW from the real sidecar.

When the external environment is not enabled, these tests are deliberately skipped rather than replaced with mocks.

This distinction should remain visible in public documentation.

### Portable local layout

Documentation should use machine-independent local paths:

```text
...\GitHub\Dev\humanist-core
...\GitHub\Dev\hacp-sidecar
```

and should not publish workstation-specific user profile paths.

Example:

```powershell
cd ...\GitHub\Dev\humanist-core
.\.venv\Scripts\Activate.ps1

$env:HACP_SIDECAR_EXTERNAL="1"
$env:HACP_SIDECAR_URL="http://127.0.0.1:8080"
$env:HACP_TEST_PRIVATE_KEY="...\GitHub\Dev\humanist-core\tests\hacp-test-key.pem"
$env:HACP_TEST_SIGNER_KEY_ID="key-ed25519-test-001"
```

Private key material itself must never be committed.

---

## 13. What 100% coverage means

The current result means:

> Every executable statement counted by the configured coverage run was executed by the checked-in test suite.

The result is materially stronger than a raw percentage because the suite includes explicit tests for:

- success paths;
- negative paths;
- fail-closed behavior;
- malformed crypto input;
- missing authority fields;
- action binding;
- scope failures;
- unknown protocol decisions;
- CLI transport failures;
- canonicalization;
- signatures;
- token lifecycle defaults.

---

## 14. What 100% coverage does not mean

100% statement coverage is **not** proof that:

- the implementation has no defects;
- every branch or state combination has been explored;
- no concurrency bugs exist;
- no parser differential exists across languages;
- the cryptography has been formally verified;
- the deployment cannot be bypassed;
- the threat model is complete;
- all future HACP implementations will behave identically;
- all semantic policy decisions are correct;
- the system is production-ready by coverage alone.

For that reason, public documentation should avoid claims such as:

> HACP is secure because it has 100% coverage.

A defensible statement is:

> The current Python implementation reaches 100% statement coverage for the checked-in test suite, supplemented by negative-path tests and separate real Python ↔ Go sidecar E2E verification.

---

## 15. Why this improves user and contributor trust

For an open-source authority-control project, trust should come from reproducible evidence rather than from security marketing.

Publishing this record is useful because users and contributors can see:

1. the exact verification command;
2. the exact reference result;
3. which paths are negative-tested;
4. why some tests are skipped;
5. which tests require a real external sidecar;
6. that warnings were fixed instead of hidden;
7. that private-state tricks were avoided for coverage;
8. that duplicate implementation logic was removed;
9. what the coverage metric does and does not prove;
10. how to reproduce the environment using portable paths.

This is especially appropriate for HACP.

HACP's core proposition is that autonomous authority should be verifiable rather than assumed. Project quality claims should follow the same principle.

---

## 16. Recommended trust language

Recommended public wording:

> HACP does not ask users to trust a coverage badge. The Python implementation publishes reproducible tests for authority construction, cryptographic binding, fail-closed behavior, sidecar decision handling, and CLI transport. The current suite reaches 100% statement coverage, while real Python ↔ Go sidecar interoperability remains a separate E2E verification layer.

Shorter form:

> 100% statement coverage is a baseline, not a security proof. HACP combines coverage with negative testing, conformance, and real sidecar E2E verification.

---

## 17. Recommended next verification layers

With statement coverage complete, further effort should move to higher-value verification rather than adding redundant tests.

Recommended sequence:

### 17.1. Branch coverage

Measure whether both sides of conditionals are exercised.

### 17.2. Mutation testing

Verify that tests fail when security-relevant logic is deliberately changed.

Examples:

- invert ALLOW/DENY checks;
- remove action-hash binding;
- bypass scope validation;
- ignore expiration;
- reuse consumed token.

A surviving mutation is often more informative than a coverage percentage.

### 17.3. Property-based tests

Useful targets:

- canonicalization invariants;
- Base64url round-trips;
- action hash stability;
- scope attenuation;
- token/envelope timestamp relations.

### 17.4. Fuzzing

Targets:

- malformed JCS/JSON;
- Unicode;
- numeric edge cases;
- nested payloads;
- oversized headers;
- duplicate/ambiguous fields;
- invalid Base64url;
- parser differential cases.

### 17.5. Cross-language differential conformance

Run identical vectors against:

- Python;
- Go;
- TypeScript;
- sidecar.

### 17.6. Negative real-sidecar E2E

Required scenarios should include:

```text
missing credentials        → DENY
tampered envelope          → DENY
tampered token             → DENY
wrong action hash          → DENY
expired authority          → DENY
revoked authority          → DENY
scope escalation           → DENY / REAUTHORIZE
semantic boundary          → CHECKPOINT
budget exhaustion          → DENY / CHECKPOINT
replay                     → DENY
valid request              → ALLOW
```

### 17.7. Threat-model-driven testing

Future tests should map directly to the HACP threat model:

- malicious agent;
- compromised tool;
- stolen key;
- replay;
- stale revocation;
- sidecar bypass;
- protocol downgrade;
- confused deputy;
- delegation escalation;
- checkpoint spoofing.

---

## 18. Knowledge-base status

This document should be treated as a verification record for the current Python SDK baseline.

Suggested public repository location:

```text
docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md
```

Suggested references from:

```text
README.md
docs/README.md
docs/HUMANIST_CORE_2.0_ROADMAP.md
```

The roadmap reference should describe this work as an achieved baseline, not as completion of all Humanist Core 2.0 hardening goals.

---

## 19. Reproducibility checklist

A contributor should be able to reproduce the default verification with:

```powershell
cd ...\GitHub\Dev\humanist-core
.\.venv\Scripts\Activate.ps1

pytest tests\ --cov=humanist_core --cov-report=term-missing
```

Verified reference characteristics:

```text
324 passed
5 external-sidecar E2E tests conditionally skipped
0 failed
100% statement coverage
100% branch coverage (BrPart 0)
external real-sidecar E2E: 5/5 PASS
```

External E2E requires the Go sidecar environment and local test key material.

No workstation-specific username, private path, or private signing key should appear in public documentation.

---

## 20. Conclusion

The completed hardening phase establishes the following Python baseline:

```text
324 passed
5 external-sidecar E2E tests conditionally skipped
0 failed
100% statement coverage
100% branch coverage (BrPart 0)
external real-sidecar E2E: 5/5 PASS
```

The HACP SDK modules currently report:

```text
builders.py     100%
cli.py          100%
client.py       100%
crypto.py       100%
exceptions.py   100%
models.py       100%
```

More importantly, the coverage result corresponds to meaningful verification of:

- fail-closed behavior;
- cryptographic input handling;
- signed wire structures;
- action binding;
- token lifecycle behavior;
- scope validation;
- sidecar decisions;
- client header injection;
- CLI transport behavior.

The appropriate interpretation is therefore:

> Humanist Core now has a fully exercised Python statement baseline for the current checked-in implementation. This is a strong reproducibility and regression-control milestone, but it remains one layer in a broader assurance model that also includes conformance, negative E2E, fuzzing, mutation testing, threat modeling, and production anti-bypass controls.

---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)