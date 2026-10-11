# HACP Composition Profile

## Profile state

```text
PROFILE_STAGE=CONTROLLED_ADMISSION_STAGE_1
TARGET_BRANCH=admit/hacp-rs
STABLE_RELEASE=NO
PRODUCTION_ACTIVATION_CHANGE=NO
```

This profile records the Humanist Core `admit/hacp-rs` controlled-admission state.

It is not the final HACP 1.1.1 pre-release composition profile.

## Humanist Core identity

```text
humanist_core.package_version=0.5.0
humanist_core.source_baseline=6d9ae82ed7fefe47b395e4ef68d0a18807866473
humanist_core.wire_family=0.9
humanist_core.architecture_generation=v2.0
```

The final admission commit for this branch is intentionally not predeclared. It MUST be recorded only after successful verification and signed commit creation.

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

## Stage-2 target

After Stage-1 independent verification and an exact signed admission commit, the next controlled branch is:

```text
admit/hacp-1.1.1-pre-release
```

That stage is responsible for binding the verified Humanist Core admission identity to the exact HACP 1.1.1 pre-release composition.

No stable-release claim is made by this document.
