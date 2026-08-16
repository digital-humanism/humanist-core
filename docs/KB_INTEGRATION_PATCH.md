# Knowledge Base integration patch

Add the public document as:

```text
docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md
```

## `docs/README.md`

Add under the verification / engineering documentation section:

```markdown
- [HACP SDK Verification, Security Hardening, and 100% Test Coverage](knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md) — reproducible record of Python SDK hardening, fail-closed and negative-path tests, coverage methodology, external sidecar E2E boundaries, and assurance limitations.
```

## Root `README.md`

Suggested short addition near testing / verification status:

```markdown
### Verification

The current Python implementation reaches **100% statement coverage**
(`211 passed`, `5 external-sidecar tests conditionally skipped`, `0 warnings`)
for the checked-in suite. Coverage is treated as a regression baseline rather
than a security proof and is supplemented by negative-path tests and separate
real Python ↔ Go sidecar E2E verification.

See: [HACP SDK Verification and Test Hardening](docs/knowledge-base/HACP_SDK_VERIFICATION_AND_TEST_HARDENING.md).
```

## `docs/HUMANIST_CORE_2.0_ROADMAP.md`

Suggested addition to the current-state / completed-baseline section:

```markdown
- **Python SDK verification baseline completed:** 100% statement coverage for
  the current checked-in implementation, with explicit fail-closed,
  cryptographic, action-binding, client/CLI negative-path tests and separate
  real Python ↔ Go sidecar E2E verification. This is a baseline for further
  branch, mutation, fuzz, differential-conformance, and threat-model testing,
  not a declaration of production security.
```

## Public-path convention

Use portable repository paths only:

```text
...\GitHub\Dev\humanist-core
...\GitHub\Dev\hacp-sidecar
```

Do not publish workstation-specific usernames, profile directories, or private
key material.

---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)