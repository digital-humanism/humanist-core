# HACP Version / Build / Compatibility Matrix

## Purpose

This matrix separates identity, evidence, activation, and compatibility.

The following concepts are distinct and MUST NOT be conflated:

```text
version
source commit
release identity
composition identity
wire version
profile revision
evidence result
production activation
architecture generation
```

## Identity

| Domain | Current controlled value |
|---|---|
| Humanist Core package | `0.5.0` |
| Humanist Core frozen source baseline | `6d9ae82ed7fefe47b395e4ef68d0a18807866473` |
| Humanist Core controlled admission branch | `admit/hacp-1.1.1-pre-release` |
| Current wire family | `0.9` |
| HACP-Core profile | `v0.9.2` |
| HACP-Enforcement profile | `revision 2 / HC2-55` |
| Humanist Core architecture generation | `v2.0` |
| Rust package | `hacp-rs 0.1.1` |
| Rust owner | `hacp-spec/hacp-rs` |
| Rust placement | `REFERENCE_ONLY` |
| Humanist Core Stage-1 admission commit | `4ff4b00bd7387466e22973e6097f1ab18f5b8f9d` |
| HACP release target | `1.1.1` |
| HACP active release candidate | `1.1.1-rc.1` |
| Release candidate state | `MUTABLE` |
| Final release tag | `v1.1.1` |
| Final release tag state | `IMMUTABLE` |
| Lifecycle target | `hacp-1.1.1-pre-release` |

Repository commit SHA values remain factual evidence identities for concrete verification runs; they are not manually maintained cross-repository release-composition bindings.

## Evidence

### HACP-Core

| Implementation | Evidence |
|---|---|
| Go | 38/38 PASS |
| TypeScript | 38/38 PASS |
| Python | 38/38 PASS |
| Rust | 36/38 direct PASS + 2 adjudicated conflicts |

### HACP-Enforcement revision 2 / HC2-55

| Implementation | Evidence |
|---|---|
| Go | 55/55 PASS |
| TypeScript | 55/55 PASS |
| Python | 55/55 PASS |
| Rust | 55/55 PASS |

Core and HC2 evidence remain separate.

## Activation

| Component / capability | Humanist Core production activation |
|---|---|
| Existing Python HACP SDK runtime | Existing baseline |
| Historical Core conformance evaluator | Verification only |
| Enforcement revision-2 successor evaluator | Verification only |
| Rust reference implementation | NO |
| Rust FFI / native embedding | NO |
| Rust runtime backend | NO |
| Rust sidecar replacement | NO |

The HACP-Enforcement revision-2 successor is executable conformance code but is not part of the production request path.

## Compatibility

The controlled `admit/hacp-1.1.1-pre-release` stage preserves:

- Humanist Core package `0.5.0`;
- HACP `0.9` wire interoperability;
- HACP-Core v0.9.2 direct Python conformance;
- additive direct Python HC2-55 conformance;
- reference-only Rust placement.

It additionally associates the verified Humanist Core Stage-1 payload with the HACP 1.1.1 release train:

```text
HACP_RELEASE=1.1.1
HACP_RELEASE_CANDIDATE=1.1.1-rc.1
RC=MUTABLE
FINAL_RELEASE_TAG=v1.1.1
FINAL_RELEASE_TAG_STATE=IMMUTABLE
```

This is a pre-release release-candidate association only. It does not establish stable-release status or production-runtime activation.

## Release identity rule

The active `1.1.1-rc.1` release candidate is mutable.

The final `v1.1.1` release tag is immutable and MUST NOT be moved or rewritten.

Concrete Git commit SHA values used by verification runs are recorded as factual evidence identities.
They MUST NOT be maintained as cyclic cross-repository release-composition bindings.

Floating names such as `latest`, `current`, `HEAD`, `main`, or `origin/main` are not final release identities.

The exact Git representation of the mutable `1.1.1-rc.1` candidate is defined separately at the release-candidate representation checkpoint.
