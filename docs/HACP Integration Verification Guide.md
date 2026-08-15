# HACP Integration Verification Guide

## 1. Purpose

This document describes how to verify the integration between:

```text
humanist-core
```

and:

```text
hacp-sidecar
```

The verification covers both local Python SDK behavior and real end-to-end interoperability with the Go sidecar.

The final goal is to prove the following execution path:

```text
humanist-core
      ↓
Python HACP SDK
      ↓
IntentEnvelope + DecisionToken
      ↓
JCS + Ed25519 + SHA-256 + Base64url
      ↓
HTTP HACP headers
      ↓
hacp-sidecar
      ↓
Go evaluation pipeline
      ↓
ALLOW
```

The verification should also confirm fail-closed behavior, action binding, replay protection, and absence of regressions in the existing `humanist-core` codebase.

---

# 2. Repository Layout

The examples below assume a layout similar to:

```text
...\GitHub\Dev\
├── humanist-core\
└── hacp-sidecar\
```

Absolute machine-specific paths should not be used in documentation.

Use:

```text
...\GitHub\Dev\humanist-core
```

instead of:

```text
C:\Users\...\humanist-core
```

This keeps the instructions portable across development environments.

---

# 3. Prerequisites

Before running the integration tests, ensure that the following components are available.

## Python

A supported Python environment must be configured for `humanist-core`.

Example:

```powershell
cd ...\GitHub\Dev\humanist-core
.\.venv\Scripts\Activate.ps1
```

Verify:

```powershell
python --version
pytest --version
```

The validated environment used:

```text
Python 3.13.x
pytest 9.x
```

---

# 4. Required Python Dependencies

The `humanist-core` environment must include the packages required by the HACP SDK and tests.

Relevant dependencies include:

```text
pytest
pytest-cov
httpx
respx
cryptography
jcs
```

Verify the environment with:

```powershell
pip list
```

If project dependencies are managed through the repository configuration, install them using the project's standard dependency installation procedure.

---

# 5. Build the HACP Sidecar

Open a separate terminal.

Navigate to:

```powershell
cd ...\GitHub\Dev\hacp-sidecar
```

Build the sidecar binary using the repository's normal Go build command.

Example:

```powershell
go build -o hacp-sidecar.exe ./cmd/sidecar
```

Verify that the binary exists:

```powershell
Test-Path .\hacp-sidecar.exe
```

Expected result:

```text
True
```

---

# 6. Start the Required Sidecar Components

The E2E environment requires the HACP sidecar and its supporting test services.

The exact commands depend on the current `hacp-sidecar` repository layout.

Typical development topology:

```text
upstream service
      ↑
hacp-sidecar
      ↑
humanist-core E2E test
```

If the sidecar configuration also uses a local control-plane service, start that as well.

Run each long-running service in a separate terminal.

---

# 7. Start the Upstream Test Service

Navigate to the actual upstream deployment directory.

Example repository-relative location:

```text
...\GitHub\Dev\hacp-sidecar\deployments\upstream
```

Start the upstream service using the command defined by the current sidecar repository.

Verify that it is listening on the configured upstream port.

---

# 8. Start the Control-Plane Service

If required by the current sidecar configuration, start the test control-plane service from its repository-relative location.

Example:

```text
...\GitHub\Dev\hacp-sidecar\deployments\control-plane
```

Keep the process running during the E2E tests.

---

# 9. Start `hacp-sidecar`

Open another terminal:

```powershell
cd ...\GitHub\Dev\hacp-sidecar
```

Set the required runtime configuration.

Example:

```powershell
$env:HACP_SIDECAR_PORT="8080"
$env:HACP_UPSTREAM="http://localhost:8000"
$env:HACP_PROVENANCE_FLUSH_PATH="provenance.jsonl"
```

Start:

```powershell
.\hacp-sidecar.exe
```

The sidecar must remain running during the integration tests.

---

# 10. Configure `humanist-core` to Use the External Sidecar

Open the terminal containing the activated `humanist-core` virtual environment.

Navigate to:

```powershell
cd ...\GitHub\Dev\humanist-core
```

Configure the E2E test to use the already running sidecar:

```powershell
$env:HACP_SIDECAR_EXTERNAL="1"
$env:HACP_SIDECAR_URL="http://127.0.0.1:8080"
```

---

# 11. Configure the Shared Test Identity

The Python SDK and Go sidecar must use the same Ed25519 identity.

The test signer ID is:

```text
key-ed25519-test-001
```

The deterministic test seed used by the Go implementation is derived from:

```text
hacp-conformance-v0.9-key-001
```

The Go implementation constructs the key using the equivalent of:

```text
SHA-256("hacp-conformance-v0.9-key-001")
        ↓
32-byte Ed25519 seed
```

Python must use the same seed.

---

# 12. Generate the Test Private Key

If the PEM file does not already exist, generate it from Python.

From:

```text
...\GitHub\Dev\humanist-core
```

run:

```powershell
python -c "import hashlib; from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; from cryptography.hazmat.primitives import serialization; seed=hashlib.sha256(b'hacp-conformance-v0.9-key-001').digest(); key=Ed25519PrivateKey.from_private_bytes(seed); open('tests\hacp-test-key.pem','wb').write(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))"
```

Verify:

```powershell
Test-Path .\tests\hacp-test-key.pem
```

Expected:

```text
True
```

---

# 13. Configure the Test Key

Set:

```powershell
$env:HACP_TEST_PRIVATE_KEY="...\GitHub\Dev\humanist-core\tests\hacp-test-key.pem"
$env:HACP_TEST_SIGNER_KEY_ID="key-ed25519-test-001"
```

Verify the private-key path:

```powershell
Test-Path $env:HACP_TEST_PRIVATE_KEY
```

Expected:

```text
True
```

---

# 14. Verify the HACP SDK Unit Tests

Before running the real sidecar integration, verify the local HACP SDK.

Run:

```powershell
pytest tests\unit\test_builders.py `
       tests\unit\test_client.py `
       tests\unit\test_crypto.py `
       tests\unit\test_jcs.py `
       -vv --tb=short
```

Expected result:

```text
21 passed
```

These tests validate:

```text
EnvelopeBuilder
TokenBuilder
SidecarClient
JCS canonicalization
Base64url encoding
SHA-256 hashing
Ed25519 signing
Ed25519 verification
action_hash generation
decision handling
fail-closed behavior
```

A failure at this stage normally indicates a Python SDK regression and should be fixed before debugging cross-language interoperability.

---

# 15. Run the HACP E2E Integration Tests

Run:

```powershell
pytest tests\test_hacp_sidecar_integration.py -vv -rs --tb=long
```

Expected result:

```text
5 passed
```

The integration suite should contain the following tests:

```text
test_real_sidecar_is_fail_closed_without_hacp_headers
test_http_action_hash_matches_sidecar_shape
test_python_envelope_and_token_signatures_are_self_consistent
test_real_sidecar_allows_python_signed_request
test_sidecar_client_gets_allow
```

---

# 16. What Each E2E Test Proves

## `test_real_sidecar_is_fail_closed_without_hacp_headers`

Verifies that the sidecar does not silently forward an unauthenticated request.

Expected behavior:

```text
request without HACP headers
        ↓
DENY
```

This confirms fail-closed behavior.

---

## `test_http_action_hash_matches_sidecar_shape`

Verifies that Python constructs the same HTTP `ProposedAction` representation used by the Go sidecar.

The action includes:

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

The token binding must satisfy:

```text
DecisionToken.action_hash
        =
SHA-256(
    JCS(HTTP ProposedAction)
)
```

This test is critical for cross-language semantic binding.

---

## `test_python_envelope_and_token_signatures_are_self_consistent`

Verifies that both:

```text
IntentEnvelope
DecisionToken
```

are correctly canonicalized and signed by the Python SDK.

The signature flow is:

```text
object
  ↓
to_dict()
  ↓
JCS
  ↓
Ed25519
```

This provides a local cryptographic baseline before the documents are sent to Go.

---

## `test_real_sidecar_allows_python_signed_request`

This is the primary interoperability test.

It sends:

```text
X-HACP-Intent-Envelope
X-HACP-Decision-Token
```

generated and signed by Python to the real Go sidecar.

Expected:

```text
X-HACP-Decision: ALLOW
HTTP 200
```

Passing this test proves that Python and Go agree on:

```text
wire schema
JCS canonicalization
Ed25519 signatures
key identity
envelope/token binding
action_hash
HTTP constraints
scope
token budget
```

---

## `test_sidecar_client_gets_allow`

Verifies the public Python SDK integration.

Instead of manually creating HTTP headers, it uses:

```python
SidecarClient
```

Expected flow:

```text
Python application
       ↓
SidecarClient
       ↓
signed IntentEnvelope
signed DecisionToken
       ↓
hacp-sidecar
       ↓
ALLOW
       ↓
httpx.Response
```

This is the closest test to real application usage.

---

# 17. Verify the Full `humanist-core` Test Suite

After the HACP E2E suite passes, run the entire project:

```powershell
pytest tests\ -vv --tb=short
```

Expected current result:

```text
148 passed
```

This verifies that HACP integration changes have not introduced regressions into existing `humanist-core` functionality.

---

# 18. Verify Full Coverage

Run:

```powershell
pytest tests\ --cov=humanist_core --cov-report=term-missing
```

Current validated result:

```text
148 passed
91% overall coverage
```

The lower overall percentage is caused by the new HACP SDK modules, especially the currently untested CLI.

---

# 19. Verify Existing Core Coverage

The existing internal core should remain at 100%.

Current validated modules:

```text
humanist_core/authority.py                         100%
humanist_core/boundary.py                          100%

humanist_core/evaluation/__init__.py               100%
humanist_core/evaluation/benchmark.py              100%
humanist_core/evaluation/metrics.py                100%

humanist_core/integrations/langchain_guard.py      100%
humanist_core/integrations/langchain_v2.py         100%

humanist_core/loop_breaker.py                      100%
humanist_core/provenance.py                        100%
humanist_core/safe_harbor.py                       100%
```

If any of these modules drop below 100%, the change should be treated as a core coverage regression.

---

# 20. Current HACP SDK Coverage

Current coverage:

```text
humanist_core/hacp/__init__.py       100%
humanist_core/hacp/builders.py        92%
humanist_core/hacp/cli.py              0%
humanist_core/hacp/client.py          86%
humanist_core/hacp/crypto.py          80%
humanist_core/hacp/exceptions.py     100%
humanist_core/hacp/models.py          99%
```

The next major coverage target should be:

```text
hacp/cli.py
```

---

# 21. Diagnosing Common Failures

## `INVALID_ENVELOPE`

Typical causes:

```text
missing required HACP field
wrong scalar/array representation
missing DecisionToken header
missing policy_digest
wire-format mismatch
```

Inspect the sidecar response body.

Example:

```json
{
  "decision": "DENY",
  "reason": "INVALID_ENVELOPE",
  "error": "..."
}
```

The `error` field usually identifies the exact parser failure.

---

# 22. `SIGNATURE_FAILURE`

This reason may indicate more than a raw Ed25519 failure.

Possible causes include:

```text
wrong public/private key pair
canonicalization mismatch
modified signed document
action_hash mismatch
token/action binding failure
```

Always inspect the detailed sidecar error.

For example:

```text
action_hash mismatch:
expected=<sidecar hash>
token=<token hash>
```

means Ed25519 may already be correct and the actual failure is semantic action binding.

---

# 23. `BUDGET_EXHAUSTED`

This usually means the same `token_id` has already consumed its allowed number of uses.

Example:

```text
max_uses = 1
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

For independent test requests, generate a new token ID:

```python
str(uuid.uuid4())
```

Do not assume that recreating the Python object creates a new authorization token.

---

# 24. Missing Sidecar

If the E2E test is skipped with a message similar to:

```text
Real sidecar E2E requires startup arguments
```

verify:

```powershell
$env:HACP_SIDECAR_EXTERNAL
$env:HACP_SIDECAR_URL
```

Expected:

```text
HACP_SIDECAR_EXTERNAL=1
HACP_SIDECAR_URL=http://127.0.0.1:8080
```

Also verify that the port is actually listening.

---

# 25. Missing Test Key

If signed tests are skipped, verify:

```powershell
$env:HACP_TEST_PRIVATE_KEY
$env:HACP_TEST_SIGNER_KEY_ID
```

Then:

```powershell
Test-Path $env:HACP_TEST_PRIVATE_KEY
```

Expected:

```text
True
```

Signer ID:

```text
key-ed25519-test-001
```

---

# 26. Recommended Verification Order

Use the following order when validating changes.

## Step 1 — Python SDK unit tests

```powershell
pytest tests\unit\test_builders.py `
       tests\unit\test_client.py `
       tests\unit\test_crypto.py `
       tests\unit\test_jcs.py `
       -vv --tb=short
```

Expected:

```text
21 passed
```

## Step 2 — Real HACP E2E

```powershell
pytest tests\test_hacp_sidecar_integration.py -vv -rs --tb=long
```

Expected:

```text
5 passed
```

## Step 3 — Full regression suite

```powershell
pytest tests\ -vv --tb=short
```

Expected:

```text
148 passed
```

## Step 4 — Coverage

```powershell
pytest tests\ --cov=humanist_core --cov-report=term-missing
```

Expected baseline:

```text
148 passed
91% total coverage
existing internal core: 100%
```

---

# 27. Quick Verification Checklist

* [ ] Python virtual environment is active.
* [ ] `hacp-sidecar` is built.
* [ ] Upstream test service is running.
* [ ] Control-plane service is running if required.
* [ ] `hacp-sidecar` is running.
* [ ] `HACP_SIDECAR_EXTERNAL=1`.
* [ ] `HACP_SIDECAR_URL` points to the running sidecar.
* [ ] Test Ed25519 PEM exists.
* [ ] `HACP_TEST_PRIVATE_KEY` points to the PEM.
* [ ] `HACP_TEST_SIGNER_KEY_ID=key-ed25519-test-001`.
* [ ] HACP unit suite reports `21 passed`.
* [ ] HACP E2E suite reports `5 passed`.
* [ ] Full suite reports `148 passed`.
* [ ] Existing internal core remains at 100% coverage.
* [ ] Overall project coverage is at or above the current baseline.

---

# 28. Expected Successful State

A fully successful verification should produce:

```text
HACP SDK unit tests                   21/21 PASS
HACP Sidecar E2E                       5/5 PASS
Full humanist-core suite             148/148 PASS
Existing core coverage                 100%
Overall project coverage                91%+
```

The critical interoperability signal is:

```text
test_real_sidecar_allows_python_signed_request PASSED
```

followed by:

```text
test_sidecar_client_gets_allow PASSED
```

Together, these prove both low-level wire interoperability and real public-SDK integration.

---

# 29. Security Properties Verified by the Procedure

This procedure validates more than simple HTTP connectivity.

It verifies:

```text
fail-closed request handling
HACP wire-schema compatibility
JCS interoperability
Ed25519 Python ↔ Go interoperability
shared signer identity
DecisionToken binding
HTTP action_hash compatibility
scope enforcement path
constraint enforcement path
token usage accounting
replay protection
SidecarClient decision handling
```

Therefore, a passing E2E suite is evidence that the HACP protocol boundary between `humanist-core` and `hacp-sidecar` is functioning as designed.

---

# 30. Maintenance Recommendation

This verification procedure should be run after changes to any of the following:

```text
IntentEnvelope schema
DecisionToken schema
Scope representation
Constraints
JCS implementation
Ed25519 handling
Base64url encoding
ProposedAction synthesis
action_hash calculation
HTTP header format
SidecarClient
sidecar evaluation pipeline
token budget logic
```

For CI, the recommended long-term structure is:

```text
Stage 1: unit tests
Stage 2: HACP conformance tests
Stage 3: HACP Sidecar E2E
Stage 4: full regression suite
Stage 5: coverage gates
```

This ensures that local implementation correctness and cross-language protocol interoperability are validated independently.

---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)