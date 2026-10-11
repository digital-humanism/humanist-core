# HACP Multi-Language Conformance Status

## Scope

This document records independently reportable HACP Family-A conformance evidence.

It does not combine evidence families into a synthetic aggregate score.

Family B diagnostic behavior is outside the scope of this record and is not used here as a release gate.

## HACP-Core

| Implementation | Evidence |
|---|---|
| Go | 38/38 PASS |
| TypeScript | 38/38 PASS |
| Python | 38/38 PASS |
| Rust | 36/38 direct PASS + 2 adjudicated conflicts |

The Rust result MUST NOT be represented as `38/38 direct`.

## HACP-Enforcement revision 2 / HC2-55

| Implementation | Evidence |
|---|---|
| Go | 55/55 PASS |
| TypeScript | 55/55 PASS |
| Python | 55/55 PASS |
| Rust | 55/55 PASS |

Four implementations independently pass the 55-vector HACP-Enforcement revision 2 HC2 request-binding evidence profile.

HC2-55 is bounded HACP-Enforcement revision-2 HTTP request-binding conformance evidence.

It is not:

- HACP-Core;
- a replacement for the Core-38 canonical baseline;
- a claim that all possible Enforcement revision-2 behavior is covered;
- a general URI-normalization conformance suite.

## Humanist Core direct Python evidence

The current controlled admission branch contains two separate Python conformance surfaces:

```text
HACP-Core / Core-38
38/38 PASS
```

and:

```text
HACP-Enforcement revision 2 / HC2-55
55/55 PASS
```

These results remain independently reportable and MUST NOT be collapsed into a synthetic combined Core-plus-HC2 score.

## Rust placement

```text
package=hacp-rs
version=0.1.1
owner=hacp-spec/hacp-rs
role=REFERENCE_ONLY
```

Rust is not activated as a Humanist Core production backend, FFI component, native embedded runtime, implementation selector entry, or sidecar replacement.

## Claim boundary

This record describes conformance evidence.

It does not by itself establish:

- production activation;
- package release status;
- final release status for the HACP 1.1.1 line;
- architectural generation;
- wire-version migration;
- security proof.
