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
| Humanist Core controlled admission branch | `admit/hacp-rs` |
| Current wire family | `0.9` |
| HACP-Core profile | `v0.9.2` |
| HACP-Enforcement profile | `revision 2 / HC2-55` |
| Humanist Core architecture generation | `v2.0` |
| Rust package | `hacp-rs 0.1.1` |
| Rust owner | `hacp-spec/hacp-rs` |
| Rust placement | `REFERENCE_ONLY` |

The branch name is workflow state, not an immutable composition identity.

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

The controlled `admit/hacp-rs` stage establishes:

- preservation of Humanist Core package `0.5.0`;
- preservation of HACP `0.9` wire interoperability;
- preservation of HACP-Core v0.9.2 direct Python conformance;
- additive direct Python HC2-55 conformance;
- reference-only Rust placement.

It does not yet activate the HACP 1.1.1 pre-release composition identity.

That immutable composition binding belongs to the subsequent controlled `admit/hacp-1.1.1-pre-release` stage.

## Immutable identity rule

Production or release profiles MUST use explicit immutable identities.

The following are not valid immutable source pins:

```text
latest
current
HEAD
main
origin/main
```

Branch names may describe workflow state but MUST NOT replace immutable commit identities in a release composition.
