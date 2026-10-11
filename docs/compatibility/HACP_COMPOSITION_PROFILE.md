# HACP Composition Profile

## Profile state

```text
PROFILE_STAGE=CONTROLLED_ADMISSION_STAGE_2
TARGET_BRANCH=admit/hacp-1.1.1-pre-release
STABLE_RELEASE=NO
PRODUCTION_ACTIVATION_CHANGE=NO
```

This profile records the Humanist Core `admit/hacp-1.1.1-pre-release` controlled-admission state.

It binds the verified Humanist Core Stage-1 admission payload to the exact immutable HACP 1.1.1 pre-release composition. It does not establish stable-release or production-activation status.

## Humanist Core identity

```text
humanist_core.package_version=0.5.0
humanist_core.source_baseline=6d9ae82ed7fefe47b395e4ef68d0a18807866473
humanist_core.wire_family=0.9
humanist_core.architecture_generation=v2.0
```

The verified Stage-1 Humanist Core payload source is:

`	ext
humanist_core.stage1_admission_commit=4ff4b00bd7387466e22973e6097f1ab18f5b8f9d
`

The final Stage-2 admission commit is intentionally not predeclared. It MUST be recorded only after successful verification and signed commit creation.

## Conformance component identities

```text
core.component=historical HACP-Core v0.9.2 Python conformance evaluator
core.component_state=PRESERVED

enforcement.component=HACP Enforcement revision 2 Python conformance evaluator
enforcement.component_state=ADDITIVE_VERSIONED_SUCCESSOR
enforcement.production_runtime_activation=NO
```

## Family-A evidence

```text
family_a.core.python=38/38 PASS
family_a.hc2.python=55/55 PASS
```

The evidence families are separate and MUST NOT be aggregated.

## Rust identity and placement

```text
rust.package_name=hacp-rs
rust.package_version=0.1.1
rust.source_owner=hacp-spec/hacp-rs
rust.role=REFERENCE_ONLY

rust.source_copy=NO
rust.vendoring=NO
rust.ffi=NO
rust.native_embedding=NO
rust.as_humanist_core_backend=NO
rust.as_sidecar_replacement=NO
rust.as_implementation_selector_entry=NO
rust.production_activation_in_humanist_core=NO
```

A separate Rust source commit is not invented by this Stage-1 profile.

## HACP 1.1.1 pre-release composition binding

`	ext
hacp.release=1.1.1
hacp.composition_id=HACP-1.1.1-spec-3ea4adc-sidecar-1bc10ac
hacp.spec_commit=3ea4adcbf6ef2548e41d340709945326026a73b6
hacp.sidecar_implementation_commit=1bc10acbe79620a165cee573c5b260cd8639280f
hacp.lifecycle_target=hacp-1.1.1-pre-release
`

This exact immutable target composition is bound to the verified Humanist Core Stage-1 payload.

This binding does not change the Humanist Core package version, wire family, architecture generation, production request path, or Rust reference-only placement.

No stable-release claim is made by this document.
