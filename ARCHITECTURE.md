# humanist-core Architecture

This file is the architecture entry point for `humanist-core`.

## Current Architecture

The current architecture is:

**Humanist Core — Architecture v2.0**  
**Working title:** Human Agency Continuity Protocol (HACP)

Read:

[`docs/ARCHITECTURE_v2.0.md`](docs/ARCHITECTURE_v2.0.md)

The central trust model is:

> An autonomous system MAY act without continuous human presence, but MUST NOT cross a meaningful boundary without renewed human authority.

HACP therefore treats human agency as a **continuity property of autonomous execution**, rather than attempting to prove continuous biological-human presence.

## Current Implementation Status

The repository currently implements and tests:

- bounded authority (`IntentEnvelope`, `DecisionToken`, `ScopeGuard`);
- semantic-boundary detection;
- risk-weighted autonomy budgets;
- causal provenance;
- LangChain runtime integration;
- Python HACP SDK;
- HACP v0.9 wire serialization;
- JCS canonicalization;
- Ed25519 signatures;
- HTTP action binding through `action_hash`;
- real Python ↔ Go `hacp-sidecar` interoperability.

A signed Python `IntentEnvelope` + `DecisionToken` request has been verified end-to-end against the real Go sidecar and reaches `ALLOW`.

The full Humanist Core Architecture v2.0 reference implementation remains in progress.

## Legacy Prototype Architecture

The original architecture explored:

- M2M loop detection;
- fixed autonomous-hop limits;
- cognitive-load heuristics;
- digital-block similarity;
- tamper-evident intent logging;
- biological-human-presence heuristics.

That architecture is retained for historical and research context as:

[`docs/ARCHITECTURE_v0.1.md`](docs/ARCHITECTURE_v0.1.md)

It should **not** be interpreted as the current trust model.

In particular:

```text
Current HACP trust model:
    authority continuity
    + bounded scope
    + semantic boundaries
    + risk
    + provenance

Legacy prototype trust model:
    human-presence / masquerade heuristics
    + fixed hop counting
```

## Version, Evidence, and Composition Identity

Architecture generation is intentionally separate from package version, wire version, conformance profile, implementation source identity, evidence result, activation state, and release composition.

The current HACP release composition is `1.1.1` — **pre-release candidate**.
The approved stable HACP release remains `1.1.0`.

The controlled HACP conformance and compatibility records are:

- [`docs/conformance/HACP_MULTI_LANGUAGE_CONFORMANCE_STATUS.md`](docs/conformance/HACP_MULTI_LANGUAGE_CONFORMANCE_STATUS.md)
- [`docs/compatibility/HACP_VERSION_BUILD_COMPATIBILITY_MATRIX.md`](docs/compatibility/HACP_VERSION_BUILD_COMPATIBILITY_MATRIX.md)
- [`docs/compatibility/HACP_COMPOSITION_PROFILE.md`](docs/compatibility/HACP_COMPOSITION_PROFILE.md)

The Rust `hacp-rs` implementation is represented here only through reference/conformance identity. It is not a Humanist Core production runtime backend.

## Implementation and Verification

For the implemented Python ↔ Go integration, see:

- [`docs/Integration with HACP Sidecar.md`](docs/Integration%20with%20HACP%20Sidecar.md)
- [`docs/HACP Integration Verification Guide.md`](docs/HACP%20Integration%20Verification%20Guide.md)

For the documentation index, see:

[`docs/README.md`](docs/README.md)

---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)