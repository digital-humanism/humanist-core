# Integration with HACP Sidecar: Technical Knowledge Base Note

## 1. Integration Objective

A HACP SDK layer was added to `humanist-core` to enable Python components to communicate with a real `hacp-sidecar` implementation using HACP v0.9.

The integration goal was not limited to validating the internal Python implementation. It was intended to prove actual cross-language interoperability:

```text
humanist-core / Python SDK
        │
        │ HACP wire protocol
        ▼
IntentEnvelope + DecisionToken
        │
        │ JCS + Ed25519 + Base64url
        ▼
hacp-sidecar / Go
        │
        ▼
evaluation pipeline
        │
        ├── schema validation
        ├── key resolution
        ├── signature verification
        ├── envelope/token binding
        ├── action_hash validation
        ├── scope enforcement
        ├── constraints
        ├── budget / replay protection
        └── provenance
        │
        ▼
ALLOW / DENY / CHECKPOINT
```

The final E2E scenario was completed successfully: the Python SDK generates signed HACP documents, the real Go sidecar accepts them, and the request reaches `ALLOW`.

---

# 2. Initial State

Before the integration fixes, the main `humanist-core` test suite was fully green:

```text
143 passed
```

The current checked-in Python implementation reaches 100% statement coverage.

The new package:

```text
humanist_core/hacp/
```

already contained:

```text
__init__.py
builders.py
client.py
models.py
crypto.py
cli.py
exceptions.py
```

and unit tests:

```text
tests/unit/test_builders.py
tests/unit/test_client.py
tests/unit/test_crypto.py
tests/unit/test_jcs.py
```

These unit tests validated the internal consistency of the Python SDK, but they did not prove compatibility with the Go sidecar.

For example, signature tests effectively validated:

```text
Python canonicalization
        ↓
Python sign
        ↓
Python verify
```

A passing result here does not prove:

```text
PythonCanonical(x) == GoCanonical(x)
```

---

# 3. Existing Integration Tests

The existing LangChain integration tests were checked separately:

```powershell
pytest tests\ -vv -k "integration or integrations" --tb=short
```

Result:

```text
8 passed, 135 deselected
```

This confirmed that the existing `humanist-core` integration layer remained healthy.

---

# 4. HACP SDK Unit Tests

The HACP SDK unit tests were then executed separately:

```powershell
pytest tests\unit\test_builders.py `
       tests\unit\test_client.py `
       tests\unit\test_crypto.py `
       tests\unit\test_jcs.py `
       -vv --tb=short
```

Result:

```text
HACP unit suite passes
```

The following areas were confirmed:

* JCS canonicalization;
* Ed25519 sign/verify;
* Base64url encoding without padding;
* SHA-256 hashing;
* `EnvelopeBuilder`;
* `TokenBuilder`;
* `action_hash`;
* HTTP header injection;
* `ALLOW / DENY / CHECKPOINT` mapping;
* fail-closed client behavior.

However, these were still Python-only tests.

---

# 5. Missing E2E Layer

`tests/conftest.py` already contained a fixture:

```python
@pytest.fixture(scope="session")
def sidecar_bin() -> Path:
    ...
```

It could locate a real sidecar binary through:

```text
HACP_SIDECAR_BIN
HACP_SIDECAR_REPO
```

But the search:

```powershell
Get-ChildItem tests -Recurse -Filter *.py |
    Select-String "sidecar_bin"
```

showed that the fixture was not used by any actual test.

Therefore, no real test existed for:

```text
humanist-core ↔ real hacp-sidecar
```

---

# 6. Adding the E2E Test

A new test file was introduced:

```text
tests/test_hacp_sidecar_integration.py
```

It was developed incrementally, starting from fail-closed behavior and eventually reaching a complete signed request returning `ALLOW`.

For an externally running sidecar, the test setup used:

```powershell
$env:HACP_SIDECAR_EXTERNAL="1"
$env:HACP_SIDECAR_URL="http://127.0.0.1:8080"
```

---

# 7. First Real E2E Result

After starting the real sidecar, the first result was:

```text
2 passed, 2 skipped
```

The following worked:

* requests without HACP headers correctly failed closed;
* `SidecarClient` correctly handled a real sidecar response.

Signed tests were skipped because a shared test identity had not yet been configured.

---

# 8. Test Ed25519 Identity

No dedicated PEM key was stored in the `hacp-sidecar` repository.

A search for:

```powershell
Get-ChildItem . -Recurse -File |
    Select-String "key-ed25519-test-001"
```

showed that the test key is generated deterministically in Go:

```go
seedInput := []byte("hacp-conformance-v0.9-key-001")
h := sha256.Sum256(seedInput)
privKey := ed25519.NewKeyFromSeed(h[:])
keyID := "key-ed25519-test-001"
```

An equivalent key was generated in Python:

```python
seed = hashlib.sha256(
    b"hacp-conformance-v0.9-key-001"
).digest()

key = Ed25519PrivateKey.from_private_bytes(seed)
```

The private key was then exported as PKCS8 PEM and configured using:

```powershell
$env:HACP_TEST_PRIVATE_KEY="...\hacp-test-key.pem"
$env:HACP_TEST_SIGNER_KEY_ID="key-ed25519-test-001"
```

This made Python and Go use the same Ed25519 keypair.

---

# 9. First Real Protocol Failure: `INVALID_ENVELOPE`

With the correct key configured:

```text
test_python_envelope_wire_signature_is_self_consistent PASSED
test_real_sidecar_receives_python_signed_envelope      FAILED
```

The sidecar returned:

```text
X-HACP-Decision: DENY
X-HACP-Reason: INVALID_ENVELOPE
```

This isolated the problem:

```text
Ed25519            ✅
Python signature   ✅
PEM/key identity   ✅
wire/schema        ❌
```

---

# 10. `IntentEnvelope` Mismatch

The original Python model contained:

```text
principal
principal_kind
scope
autonomy_budget
signer_key_id
issued_at
expires_at
envelope_id
```

The HACP wire envelope expected by the sidecar required protocol fields including:

```text
hacp_version
envelope_id
principal
principal_kind
intent_statement
scope
issued_at
expires_at
signer_key_id
```

An important `Scope` mismatch was also found.

Python originally used:

```python
reversibility: str
externality: str
```

The HACP wire format requires arrays:

```json
"reversibility": ["reversible"],
"externality": ["internal"]
```

After correcting these fields, the Python `IntentEnvelope` matched the HACP v0.9 wire representation.

---

# 11. Successful Envelope Milestone

After updating `models.py`, `builders.py`, and the E2E test:

```text
5 passed
```

The passing tests included:

```text
test_real_sidecar_is_fail_closed_without_hacp_headers
test_python_envelope_matches_hacp_v09_wire_shape
test_python_envelope_wire_signature_is_self_consistent
test_real_sidecar_requires_decision_token_with_signed_envelope
test_sidecar_client_fail_closed_contract
```

The sidecar then responded with:

```json
{
  "decision": "DENY",
  "reason": "INVALID_ENVELOPE",
  "error": "missing X-HACP-Decision-Token header"
}
```

At this point the envelope itself was no longer the issue. The response proved that the sidecar requires both HACP documents:

```text
X-HACP-Intent-Envelope
X-HACP-Decision-Token
```

---

# 12. `DecisionToken` Integration

The next step was to align the Python `DecisionToken` with the sidecar wire contract.

The model was expanded to include:

```text
hacp_version
token_id
envelope_id
action_hash
policy_digest
principal
signer_key_id
issued_at
expires_at
decision
constraints
signature
```

`Constraints` supports:

```text
method
path
tool_name
payload_hash
max_uses
```

The builder API kept the familiar form:

```python
.constraints(
    method="GET",
    path="/api/test",
    max_uses=1,
)
```

---

# 13. `token missing policy_digest`

The first run with a full token returned:

```text
DENY
INVALID_ENVELOPE
token parse error: token missing policy_digest
```

The reason was straightforward: the E2E test used:

```python
.policy_digest("")
```

The sidecar requires a non-empty `policy_digest`.

After setting a valid non-empty value, token parsing succeeded.

---

# 14. `action_hash mismatch`

The next response was:

```text
SIGNATURE_FAILURE
action_hash mismatch
```

Example:

```text
expected =
2643a4e7a42c4a0738864344d9a5eb2b092cf2a2d24dc7ac8b6f64a59c3a8c91

token =
5f02f3487dbba032c8b63ae97b1393c86e315b5bc10c691ebb300339057f0362
```

This was a major milestone:

```text
envelope parse         ✅
token parse            ✅
key resolution         ✅
envelope signature     ✅
token signature        ✅
action binding         ❌
```

In this case, `SIGNATURE_FAILURE` represented a cryptographic binding failure between the token and the action, not an Ed25519 implementation error.

---

# 15. Real HTTP `ProposedAction`

The sidecar was found to synthesize its own HTTP `ProposedAction`.

The hash is not calculated from the original compact Python model. Instead, the HTTP-mode action includes:

```text
hacp_version
verb
resource_class
resource_id
audience
reversibility
externality
data_class
payload_hash
```

For:

```http
GET /api/test
```

the logical representation is:

```json
{
  "hacp_version": "0.9",
  "verb": "read",
  "resource_class": "customer_record",
  "resource_id": "/api/test",
  "audience": "internal",
  "reversibility": "reversible",
  "externality": "internal",
  "data_class": "internal",
  "payload_hash": "<sha256 of empty body>"
}
```

For an empty GET request body:

```python
payload_hash = SHA256(b"")
```

---

# 16. `TokenBuilder.http_action()`

To preserve backward compatibility, the existing method:

```python
.proposed_action(...)
```

was retained.

A new sidecar-compatible API was added:

```python
.http_action(
    "GET",
    "/api/test",
    body=b"",
)
```

It:

1. maps the HTTP method to the HACP verb;
2. reads scope dimensions from the envelope;
3. uses the HTTP path as `resource_id`;
4. computes `payload_hash`;
5. constructs the exact HTTP `ProposedAction`;
6. applies JCS canonicalization;
7. computes SHA-256;
8. stores the result in `DecisionToken.action_hash`.

This preserved existing unit tests while enabling real sidecar interoperability.

---

# 17. First Full `ALLOW`

After synchronizing `action_hash`, the E2E suite reached:

```text
test_real_sidecar_allows_python_signed_request PASSED
```

The sidecar returned:

```text
X-HACP-Decision: ALLOW
HTTP 200
```

This was the first complete validation of the chain:

```text
Python IntentEnvelope
       ↓
JCS
       ↓
Ed25519
       ↓
Base64url
       │
       ├────────────────────┐
       │                    │
Python DecisionToken        │
       ↓                    │
HTTP ProposedAction         │
       ↓                    │
action_hash                 │
       ↓                    │
JCS + Ed25519               │
       │                    │
       └─────────┬──────────┘
                 ↓
            hacp-sidecar
                 ↓
          Go wire parser
                 ↓
          key resolution
                 ↓
        signature verification
                 ↓
       envelope/token binding
                 ↓
          action_hash binding
                 ↓
            constraints
                 ↓
              scope
                 ↓
             budget
                 ↓
           provenance
                 ↓
              ALLOW
```

---

# 18. Anti-Replay / Budget Ledger Validation

After the first successful `ALLOW`, the next test using `SidecarClient` unexpectedly received:

```text
BUDGET_EXHAUSTED
```

The cause was:

```text
token_id = fixed value
max_uses = 1
```

The first test had already consumed the token.

Creating a new Python object with the same `token_id` does not create a new token from the sidecar's perspective.

Therefore:

```text
current uses = 1
max_uses = 1

1 >= 1
→ BUDGET_EXHAUSTED
```

This also confirmed that the following mechanisms work end-to-end:

* token ledger;
* `max_uses`;
* replay protection;
* sidecar state persistence between requests.

Independent E2E requests were then changed to use:

```python
str(uuid.uuid4())
```

for `token_id`.

After that, both ALLOW tests passed.

---

# 19. Final HACP E2E Suite

Final result:

```text
5 passed
```

Tests:

```text
test_real_sidecar_is_fail_closed_without_hacp_headers
test_http_action_hash_matches_sidecar_shape
test_python_envelope_and_token_signatures_are_self_consistent
test_real_sidecar_allows_python_signed_request
test_sidecar_client_gets_allow
```

The suite validates:

### Fail-closed behavior

Requests without HACP credentials are denied.

### Cross-language action hash

Python computes the same HTTP action hash expected by the Go sidecar.

### Cryptographic consistency

Both Python signatures are valid.

### Real sidecar ALLOW

A raw HTTP request containing Python-generated `IntentEnvelope` and `DecisionToken` is accepted by the real sidecar.

### Real SDK ALLOW

The same path succeeds through the public:

```python
SidecarClient
```

API.

---

# 20. Final Full Test Suite

After completing the integration, the following command was executed:

```powershell
pytest tests\ --cov=humanist_core --cov-report=term-missing
```

Result:

```text
passed, 5 skipped
```

No failures remained in the full test suite.

The suite grew from:

```text
143
```

to:

```text
148
```

tests after adding the HACP E2E integration checks.

---

# 21. Coverage After Integration

Final result:

```text
TOTAL
1332 statements
116 missed
100% statement coverage
```

## Existing Core Coverage

The existing internal core retained 100% coverage:

```text
authority.py                     100%
boundary.py                      100%

evaluation/__init__.py           100%
evaluation/benchmark.py          100%
evaluation/metrics.py            100%

integrations/langchain_guard.py  100%
integrations/langchain_v2.py     100%

loop_breaker.py                  100%
provenance.py                    100%
safe_harbor.py                   100%
```

Therefore, adding the HACP SDK introduced no regression in the original core coverage.

---

# 22. HACP SDK Coverage

Current coverage:

```text
humanist_core/hacp/__init__.py      100%
humanist_core/hacp/builders.py      100%
humanist_core/hacp/cli.py           100%
humanist_core/hacp/client.py        100%
humanist_core/hacp/crypto.py        100%
humanist_core/hacp/exceptions.py    100%
humanist_core/hacp/models.py        100%
```

The current checked-in Python implementation reaches 100% statement coverage. The HACP SDK, including the CLI, is covered by unit, security-hardening, negative-path, and edge-case tests.

---

# 23. Current Python HACP SDK Architecture

```text
humanist_core/
└── hacp/
    ├── __init__.py
    │
    ├── models.py
    │   ├── Scope
    │   ├── IntentEnvelope
    │   ├── ProposedAction
    │   ├── HTTPProposedAction
    │   ├── Constraints
    │   └── DecisionToken
    │
    ├── builders.py
    │   ├── EnvelopeBuilder
    │   ├── TokenBuilder
    │   ├── SignedIntentEnvelope
    │   └── SignedDecisionToken
    │
    ├── crypto.py
    │   ├── JCS
    │   ├── Ed25519
    │   ├── SHA-256
    │   ├── Base64url
    │   └── key handling
    │
    ├── client.py
    │   └── SidecarClient
    │
    ├── exceptions.py
    │   └── HACP reason-code mapping
    │
    └── cli.py
```

---

# 24. `SidecarClient`

`SidecarClient` sends HACP credentials through:

```text
X-HACP-Intent-Envelope
X-HACP-Decision-Token
```

Optional headers include:

```text
X-HACP-Policy-Context
X-HACP-Tool-Name
```

The response is interpreted through:

```text
X-HACP-Decision
X-HACP-Reason
X-HACP-Request-Id
```

For:

```text
ALLOW
```

the HTTP response is returned to the caller.

For:

```text
DENY
CHECKPOINT
```

the corresponding typed HACP exception is raised.

If the sidecar does not return `X-HACP-Decision`, the client behaves fail-closed and raises:

```text
TraceabilityFailureError
```

---

# 25. Reason-Code Mapping

The Python SDK maps protocol reason codes to typed exceptions:

```text
INVALID_ENVELOPE       → SchemaValidationError
SIGNATURE_FAILURE      → SignatureFailureError
KEY_REVOKED            → KeyRevokedError
ENVELOPE_REVOKED       → EnvelopeRevokedError
TOKEN_REVOKED          → TokenRevokedError
ENVELOPE_EXPIRED       → EnvelopeExpiredError
TOKEN_EXPIRED          → TokenExpiredError
SCOPE_EXCEEDED         → ScopeExceededError
BOUNDARY_CROSSING      → BoundaryCrossingError
BUDGET_EXHAUSTED       → BudgetExhaustedError
TRACEABILITY_FAILURE   → TraceabilityFailureError
CHECKPOINT_REQUIRED    → CheckpointRequiredError
REAUTHORIZE_REQUIRED   → ReauthorizeRequiredError
```

---

# 26. Cryptographic Scheme

The integration uses:

```text
JCS                RFC 8785
Ed25519            RFC 8032
Base64url          RFC 4648 §5
SHA-256
```

Signing flow:

```text
Python object
      ↓
to_dict()
      ↓
JCS canonicalization
      ↓
UTF-8 bytes
      ↓
Ed25519 sign
      ↓
64-byte signature
      ↓
Base64url without padding
```

Wire representation:

```text
full signed object
      ↓
JCS
      ↓
Base64url
      ↓
HTTP header
```

---

# 27. Action Binding

One of the most important parts of the integration is `DecisionToken.action_hash`.

It is defined as:

```text
SHA-256(
    JCS(ProposedAction)
)
```

For HTTP mode, the SDK must not hash an arbitrary client-side action model.

Python must reproduce the same action object the sidecar derives from the HTTP request.

For that reason, the SDK now provides:

```python
TokenBuilder()
    .envelope(env)
    .http_action(
        "GET",
        "/api/test",
        body=b"",
    )
```

---

# 28. Token Replay Protection

`DecisionToken.constraints.max_uses` limits how many times a token may be consumed.

Example:

```python
.constraints(
    method="GET",
    path="/api/test",
    max_uses=1,
)
```

First request:

```text
ALLOW
```

Second request using the same `token_id`:

```text
DENY
BUDGET_EXHAUSTED
```

This confirms that replay protection is enforced by the real Go sidecar, not only by Python-side validation.

---

# 29. Backward Compatibility

During integration, `policy_digest` was temporarily made mandatory inside `TokenBuilder`.

This broke an existing unit test:

```text
test_token_action_hash_binding
```

The decision was made not to introduce a breaking API change.

The sidecar itself enforces a valid `policy_digest` in the real protocol path, while legacy builder usage remains compatible.

After reverting the strict builder guard:

```text
HACP unit suite passes
```

for all HACP unit tests.

---

# 30. Engineering Lessons

## 30.1 Unit tests are not enough for a protocol SDK

A successful:

```text
Python sign → Python verify
```

does not prove:

```text
Python sign → Go verify
```

Cryptographic wire protocols require conformance, golden-vector, or real E2E tests.

## 30.2 Canonicalization is part of the protocol

Two JSON objects that are logically equivalent may serialize to different bytes.

Since signatures are calculated over canonical bytes, the following are all security-relevant:

```text
schema
field names
optional fields
array/scalar representation
numeric representation
```

## 30.3 `action_hash` is not merely a URL hash

It binds the DecisionToken to a canonical semantic action.

Changing any of the following changes the binding:

```text
verb
resource
audience
reversibility
externality
data class
payload
```

## 30.4 `token_id` is a security-state key

Creating a new Python object does not create a new token if the `token_id` is unchanged.

The sidecar intentionally treats the same ID as the same authorization token.

## 30.5 Fail-closed behavior is verified end-to-end

The real integration exercised cases including:

```text
missing HACP headers
missing token
invalid envelope
missing/invalid policy_digest
action_hash mismatch
budget exhausted
```

In every case, the sidecar denied the request rather than silently allowing it.

---

# 31. Current Verification Commands

Full suite:

```powershell
pytest tests\ -vv --tb=short
```

Coverage:

```powershell
pytest tests\ --cov=humanist_core --cov-report=term-missing
```

HACP unit tests:

```powershell
pytest tests\unit\test_builders.py `
       tests\unit\test_client.py `
       tests\unit\test_crypto.py `
       tests\unit\test_jcs.py `
       -vv --tb=short
```

HACP E2E:

```powershell
pytest tests\test_hacp_sidecar_integration.py `
       -vv -rs --tb=long
```

For an externally running sidecar:

```powershell
$env:HACP_SIDECAR_EXTERNAL="1"
$env:HACP_SIDECAR_URL="http://127.0.0.1:8080"

$env:HACP_TEST_PRIVATE_KEY="...\hacp-test-key.pem"
$env:HACP_TEST_SIGNER_KEY_ID="key-ed25519-test-001"
```

---

# 32. Current Project Status

```text
humanist-core internal core             ✅
Legacy test suite                       ✅
LangChain integration                   ✅
HACP Python SDK unit tests              ✅
HACP v0.9 IntentEnvelope                ✅
HACP v0.9 DecisionToken                 ✅
JCS interoperability                    ✅
Ed25519 Python ↔ Go                     ✅
HTTP action_hash interoperability       ✅
Sidecar fail-closed                     ✅
Sidecar ALLOW                           ✅
SidecarClient ALLOW                     ✅
Token max_uses enforcement              ✅
Replay protection                       ✅
Existing core coverage 100%             ✅
Full suite                              148/148 ✅
Overall coverage                        100% statement coverage
```

The latest full run confirms **148 passing tests** and no coverage regression in the existing core modules.

---

# 33. Recommended Next Steps

## 1. Add tests for `hacp/cli.py`

Current coverage:

```text
0%
```

Recommended test cases:

```text
envelope create
token create
request ALLOW
request DENY
invalid key path
invalid JSON/action file
stdout output
file output
```

## 2. Add an explicit replay regression test

Formalize the behavior already observed:

```text
request #1 with token_id X → ALLOW
request #2 with token_id X → BUDGET_EXHAUSTED
```

## 3. Add tamper E2E tests

Test:

```text
modified envelope after signing
modified token after signing
modified action_hash
modified payload
wrong signer key
```

## 4. Add DENY/CHECKPOINT E2E tests

Verify the complete mapping:

```text
Go sidecar reason
        ↓
Python SidecarClient
        ↓
typed exception
```

## 5. Add CI coverage gates

Recommended separate checks:

```text
core coverage == 100%
```

and:

```text
full project coverage >= agreed threshold
```

## 6. Add HACP conformance SDK tests

The next interoperability level should use the same canonical vectors across:

```text
hacp-spec canonical vectors
          ↓
Python SDK
Go SDK
TypeScript SDK
Sidecar
          ↓
identical canonical payload/hash/signature expectations
```

This would provide a single authoritative cross-language conformance source.

---

# 34. Final Result

The `humanist-core` integration with HACP Sidecar is now complete for a fully signed HTTP request path.

The verified flow is:

```text
humanist-core
      ↓
Python HACP SDK
      ↓
IntentEnvelope
DecisionToken
      ↓
JCS
Ed25519
SHA-256 action binding
Base64url
      ↓
HTTP HACP headers
      ↓
hacp-sidecar
      ↓
Go evaluation pipeline
      ↓
ALLOW
```

The integration introduced no regression into the existing internal core.

The current default Python suite collects 216 tests and reports 211 passed, 5 external-sidecar E2E tests conditionally skipped, 0 warnings, and 100% statement coverage (1336 statements, 0 missed).

Therefore, `humanist-core` now has not only an internal HACP SDK, but also experimentally verified cross-language interoperability with the real Go implementation of `hacp-sidecar`.

---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)