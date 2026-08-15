# Humanist Core 2.0 — HACP Technology Completion Plan

**Status:** proposal / roadmap  
**Target architecture:** HACP / Architecture v2.0  
**Current implementation:** humanist-core 0.5.0-alpha + verified HACP wire v0.9 interoperability  
**Purpose:** define the boundary between the current model-validation stage and the future production-grade completion milestone called Humanist Core 2.0.

---

## 1. Purpose

The project currently has three independent version dimensions:

```text
humanist-core package version   → 0.x / 0.5.0-alpha today
HACP wire protocol version      → v0.9 today
HACP Architecture version       → v2.0 — current target architecture
```

`Architecture v2.0` already describes the target Human Agency Continuity Protocol model. The future **Humanist Core 2.0** release should mean something stronger:

> HACP Architecture v2.0 is not merely specified and partially implemented; it is technologically closed, reproducible across independent implementations, security-hardened, and suitable for production enforcement.

Until that milestone, the 0.x line should be used primarily for **model validation**: validate authority continuity, the `IntentEnvelope` / `DecisionToken` contract, Action Boundaries, Semantic Checkpoint behavior, Autonomy Budget semantics, and M2M loop breaking without turning HACP into content moderation.

---

## 2. Relationship to the Digital Humanism Manifesto

HACP does not claim to implement the entire Digital Humanism Manifesto. Its most direct technical alignment is with Principles 2, 7 and 7.1.

### Principle 2 — Priority of Intent and Graded Response

The Manifesto rejects crude binary `Ban / Block` logic and calls for responses that consider intent, context and severity.

HACP maps this idea into graded enforcement outcomes:

```text
ALLOW
ALLOW_WITH_AUDIT
CHECKPOINT
REAUTHORIZE
DENY
```

### Principle 7 — Preserving Human Agency

Humanist Core protects not continuous human presence, but **continuity of human authority**.

### Principle 7.1 — Semantic Checkpoint and Protection Against the Machine-to-Machine Loop

The Manifesto calls for an architectural barrier that recognizes blind machine-to-machine continuation, halts the chain, and restores the human right to the final meaningful decision.

This is the normative foundation for the HACP Semantic Checkpoint.

---

## 3. Core Positioning of HACP

### 3.1. HACP Is Not Content Moderation

HACP should not primarily filter user prompts, opinions, or model text.

Its task is:

> to govern the authority of an autonomous principal at the point where machine intent becomes an externally consequential action.

The core boundary is:

```text
Agent Reasoning
      ↓
Proposed Action
      ↓
──────── HACP ACTION BOUNDARY ────────
      ↓
Tool / API / MCP / Agent / External System
```

### 3.2. The Agent Is an Untrusted Principal

Within an HACP enforcement domain:

> an autonomous agent has no implicit authority.

```text
Agent wants to act
        ≠
Agent is authorized to act
```

### 3.3. HACP Is a Verifier of Authority, Not a Judge of Conscience

HACP verifies:

- the origin of authority;
- signatures;
- expiration;
- revocation;
- scope;
- action binding;
- semantic/risk boundary transitions;
- autonomy/replay budget;
- whether renewed authority is required.

It does not classify moral content.

The precise formulation is:

> **HACP verifies authority, action binding, and policy-defined semantic boundaries. It does not classify moral content.**

---

## 4. What the Current Implementation Has Already Demonstrated

Across `humanist-core` and related implementations, the project already contains:

- Authority Core;
- ScopeGuard;
- SemanticDeltaGuard;
- RiskEngine;
- AutonomyBudget;
- causal provenance;
- LangChain runtime integration;
- Python HACP SDK;
- HACP v0.9 wire models;
- JCS canonicalization;
- Ed25519 signing/verification;
- `IntentEnvelope`;
- `DecisionToken`;
- HTTP `ProposedAction`;
- `action_hash`;
- SidecarClient;
- Python ↔ Go sidecar E2E interoperability.

Verified behavior includes:

```text
missing HACP credentials      → fail closed
Python IntentEnvelope         → Go parses/verifies
Python DecisionToken          → Go parses/verifies
Python JCS                    ↔ Go-compatible canonical payload
Python Ed25519 signature      → Go verification
Python HTTP action_hash       = Go sidecar action_hash
valid signed request          → ALLOW
reused max_uses token         → BUDGET_EXHAUSTED
```

HACP therefore already has an **executable protocol skeleton**, not only an architectural proposal.

---

## 5. Current Strategy: Validate the Model First

Before 2.0, HACP should deliberately avoid expanding into every adjacent security domain.

The central question for the current stage is:

> Is the agency-management model itself strong enough to justify a production security protocol?

### Validate Now

1. **Untrusted-agent model**
   - where deny-by-default is appropriate;
   - where it creates unnecessary friction;
   - where long-running autonomy is safe.

2. **Action-boundary model**
   - whether HTTP/MCP/tool-call boundaries are sufficient;
   - which real-world actions are poorly represented.

3. **IntentEnvelope**
   - whether scope dimensions are sufficient;
   - which fields are actually necessary.

4. **DecisionToken**
   - token granularity;
   - normative constraint semantics.

5. **AutonomyBudget**
   - risk-weight calibration;
   - false-positive checkpoints;
   - dangerous actions that remain too cheap.

6. **SemanticDelta**
   - which transitions are genuinely meaningful;
   - which semantics can be structural;
   - where policy/tool metadata is required.

7. **Decision states**
   - whether `ALLOW / CHECKPOINT / REAUTHORIZE / DENY` are sufficient;
   - whether transport failures are separated from agency decisions.

8. **M2M Loop Breaking**
   - whether safe agent chains can be distinguished from loss of human agency.

### Do Not Turn HACP Into

- a prompt moderation framework;
- a universal AI safety engine;
- an IAM replacement;
- a KMS replacement;
- a SIEM;
- a service-mesh replacement;
- a universal policy language;
- a biological-human detector;
- a moral classifier;
- a workflow engine.

HACP should preserve **narrow implementation ownership**.

---

## 6. Invariants That Must Survive Into 2.0

### 6.1. No Implicit Agent Authority

```text
Agent authority = explicitly granted authority
```

### 6.2. Fail Closed

Missing, invalid, expired, revoked, action-mismatched, or out-of-scope credentials must not silently pass.

### 6.3. Action-Boundary Enforcement

The primary HACP security guarantee must not require interception of user prompts.

### 6.4. Explicit Action Binding

A `DecisionToken` must bind to a specific action or a formally defined action set.

### 6.5. Authority Attenuation

Child authority cannot exceed parent authority:

```text
child_scope ⊆ parent_scope
child_expiry ≤ parent_expiry
child_risk_budget ≤ parent_remaining_budget
```

### 6.6. Human-Governed Authority Root

A machine delegation chain must be traceable to a human-governed authority root.

This does not mean a human manually signs every action. It means:

> a machine cannot indefinitely manufacture new authority for itself.

### 6.7. Semantic Discontinuity Requires Renewed Authority

A meaningful boundary crossing must not silently inherit stale authority.

### 6.8. Cryptography Proves Authorization Facts, Not Morality

A signature proves origin and integrity of authority, not ethical correctness.

### 6.9. Deployment Must Prevent Bypass

A sidecar does not protect an upstream if the agent can reach that upstream directly.

---

# 7. Humanist Core 2.0 Scope

## 7.1. Human-Root Authority Model

Current principals may be `human`, `system`, or `delegated`. Valid machine delegation alone does not prove continuity of human agency.

2.0 should introduce a first-class `AuthorityRoot`:

```text
AuthorityRoot
    root_id
    root_kind
    governed_by
    trust_domain
    created_at
    expires_at
    policy_digest
    signer
```

Possible root kinds:

```text
human
human_governed_system
institutional
```

Every delegated authority should expose verifiable lineage:

```text
DecisionToken
    ↓
DelegatedEnvelope / DelegationGrant
    ↓
ParentEnvelope
    ↓
AuthorityRoot
```

---

## 7.2. Authority Provenance Graph

Provenance should answer not only *what happened*, but:

> Why did this principal have authority to perform this exact action?

Required causal relations may include:

```text
AUTHORIZED_BY
DELEGATED_FROM
DERIVED_FROM
CHECKPOINTED_BY
REVOKED_BY
EXECUTED_AS
```

Example:

```text
Human Root H1
     │
     └── IntentEnvelope E1
              │
              └── Delegation D1
                       │
                       └── DecisionToken T1
                                │
                                └── ProposedAction A1
                                         │
                                         └── ProvenanceEvent P1
```

The system should be able to explain:

```text
Why was A1 allowed?
Who ultimately authorized it?
Which scope constrained it?
Which delegation attenuated it?
Which checkpoint renewed it?
```

---

## 7.3. Delegation with Mandatory Attenuation

Delegation becomes a protocol primitive.

Requirements:

- child scope ≤ parent scope;
- child expiry ≤ parent expiry;
- child cannot restore revoked capabilities;
- child cannot increase budget;
- delegation depth may be policy-limited;
- delegation is signed;
- parent authority ID is in the signed payload.

Possible model:

```text
DelegationGrant
    grant_id
    parent_authority_id
    delegate_principal
    scope
    risk_budget
    not_before
    expires_at
    max_delegation_depth
    policy_digest
    signer_key_id
    signature
```

---

## 7.4. Provenance-Aware M2M Loop Breaking

Current `SemanticDeltaGuard` and `AutonomyBudget` detect useful signals, but they do not by themselves prove that execution has become a blind M2M chain.

2.0 should consider:

- authority lineage;
- delegation depth;
- last meaningful human checkpoint;
- semantic-goal continuity;
- accumulated risk;
- responsibility transitions;
- audience/externality changes;
- provenance of machine-generated delegation.

Example:

```text
root_authority = H1
last_human_checkpoint = C1
delegation_depth = 4
semantic_delta_since_C1 = high
externality = increased
risk_budget = near exhaustion

→ CHECKPOINT_REQUIRED
```

Core principle:

> An M2M loop is not merely “many agent calls.” It is a machine chain continuing meaningful synthesis or action without sufficient continuity of human authority.

---

## 7.5. Full Semantic Checkpoint Protocol

A checkpoint should become a full protocol flow rather than only an exception or stop state:

```text
PROPOSED
   ↓
EVALUATING
   ├── ALLOW ─────────→ EXECUTED
   ├── DENY ──────────→ TERMINATED
   └── CHECKPOINT
          ↓
      WAITING_FOR_HUMAN
          ↓
      HUMAN_DECISION
       ├── REJECT
       ├── MODIFY
       └── AUTHORIZE
              ↓
         NEW AUTHORITY
              ↓
            RESUME
```

A meaningful checkpoint should state:

- what changed;
- which action is proposed;
- why previous authority is insufficient;
- what new risk appeared;
- which scope expansion is requested;
- what will be authorized after approval;
- the duration and limits of renewed authority.

`Continue? [Yes]` is not sufficient.

---

## 7.6. Typed Action Semantics

The production profile must not depend on guessing an operation from a tool name.

HACP needs a typed action contract:

```json
{
  "verb": "update",
  "resource_class": "customer_record",
  "resource_id": "customer/123",
  "audience": "partner",
  "reversibility": "compensatable",
  "externality": "external",
  "data_class": "personal",
  "effects": ["write", "network_transfer"]
}
```

Tool/MCP servers should expose a machine-readable Capability Manifest:

```text
tool_name
supported_verbs
resource_classes
data_classes
possible_externalities
reversibility
effect_types
required_scopes
```

---

## 7.7. MCP-Native Enforcement

2.0 should define a native MCP boundary:

- canonical MCP action representation;
- token binding to method/tool/resource;
- deterministic payload hashing;
- response provenance;
- server capability identity;
- tool-chain handling;
- delegation-context propagation.

---

## 7.8. Cryptographic Key Lifecycle

2.0 should define:

- trust roots;
- key registration;
- rotation;
- revocation;
- compromise handling;
- grace periods;
- key usage constraints;
- environment/domain binding;
- offline verification;
- optional KMS/HSM integration.

Deployments may distinguish:

```text
signing key
policy signing key
authority-root key
service identity key
```

---

## 7.9. Formal Revocation Model

Normative rules are required for:

- signer keys;
- IntentEnvelopes;
- DecisionTokens;
- DelegationGrants;
- AuthorityRoots;
- policy versions.

The protocol must define ordering, freshness, propagation, caching, and fail-closed behavior under stale revocation state.

---

## 7.10. Protocol Versioning and Negotiation

2.0 should formalize:

- wire compatibility;
- mandatory/optional fields;
- unknown-field behavior;
- canonicalization rules;
- feature negotiation;
- downgrade policy;
- deprecation windows;
- interoperability matrix.

Principle:

> unknown security-critical semantics must not silently degrade.

---

## 7.11. Conformance as a Release Gate

One normative vector set should verify:

```text
humanist-core Python SDK
hacp-go
hacp-ts
hacp-sidecar
future implementations
```

Required vector classes:

- valid envelope;
- invalid signature;
- expiration;
- revocation;
- malformed structures;
- action_hash mismatch;
- scope violation;
- boundary crossing;
- budget exhaustion;
- replay;
- checkpoint;
- delegation attenuation;
- delegation escalation;
- broken human-root continuity;
- protocol-version mismatch.

An implementation should not claim HACP conformance unless the mandatory suite passes completely.

---

## 7.12. Negative E2E Security Matrix

2.0 should require real E2E coverage:

```text
missing headers            → DENY
tampered envelope          → DENY
tampered token             → DENY
wrong action_hash          → DENY
expired envelope           → DENY
expired token              → DENY
revoked signer             → DENY
revoked envelope           → DENY
revoked token              → DENY
scope escalation           → DENY / REAUTHORIZE
semantic boundary          → CHECKPOINT
budget exhausted           → DENY / CHECKPOINT
replay                     → DENY
delegation escalation      → DENY
broken authority lineage   → DENY / CHECKPOINT
valid request              → ALLOW
```

---

## 7.13. Property-Based and Fuzz Testing

Required areas:

- JCS property tests;
- round-trip serialization;
- malformed Base64url;
- duplicate/ambiguous fields;
- numeric edge cases;
- Unicode edge cases;
- deeply nested inputs;
- oversized payloads;
- parser fuzzing;
- action-synthesis fuzzing;
- cross-language differential testing.

---

## 7.14. Formal Enforcement Order

Verification order should become a protocol invariant:

```text
1. Parse / schema
2. Resolve trust identity
3. Revocation preconditions
4. Verify signatures
5. Validate temporal bounds
6. Validate authority lineage
7. Validate action binding
8. Validate constraints
9. Validate scope
10. Evaluate semantic boundary
11. Evaluate autonomy/replay budget
12. Record provenance
13. Forward / checkpoint / deny
```

The order should be conformance-tested because changing it may alter security semantics.

---

## 7.15. Production Anti-Bypass Profile

2.0 should require the deployment invariant:

```text
Agent cannot reach protected upstream directly.
```

Possible enforcement mechanisms include:

- Kubernetes NetworkPolicy;
- service-mesh routing;
- localhost-only upstream;
- firewalling;
- namespace/container isolation;
- egress policy;
- mTLS;
- gateway enforcement.

HACP does not need to implement these systems; it needs to define the invariant.

---

## 7.16. Privacy-Minimized Provenance

Principle:

> log authority and consequence metadata by default; log content only when policy explicitly requires it.

Prefer:

- hashes;
- resource IDs;
- effect descriptors;
- decision reasons;
- policy digests;
- encrypted or opt-in payload references.

Raw prompt/output capture should not be the default.

---

## 7.17. Threat Model

A dedicated threat-model document should exist before 2.0.

Minimum adversaries:

- malicious agent;
- compromised runtime;
- compromised tool;
- malicious MCP server;
- stolen signing key;
- replay attacker;
- sidecar bypass;
- stale revocation cache;
- policy downgrade;
- confused deputy;
- delegation escalation;
- provenance tampering;
- checkpoint spoofing;
- compromised approval UI.

For each threat:

```text
asset
trust boundary
attack
mitigation
residual risk
test
```

---

## 7.18. Policy Ownership Boundary

HACP should not become a universal policy engine.

```text
External policy / governance
        ↓
policy_digest + constraints
        ↓
HACP
        ↓
verify action against granted authority
```

HACP defines **what must be provable**. External infrastructure may decide **how policy is computed**.

---

## 7.19. Stable Reason-Code Taxonomy

2.0 should define stable machine-readable categories:

```text
AUTHENTICATION
AUTHORITY
SCOPE
BOUNDARY
REVOCATION
TEMPORAL
ACTION_BINDING
BUDGET
REPLAY
DELEGATION
PROTOCOL
INTERNAL
```

Reason codes should remain separate from human-readable diagnostics.

---

## 7.20. Observability Without Authority Leakage

Useful operational metrics include:

- decision counters;
- checkpoint rate;
- deny-reason distribution;
- verification latency;
- revocation freshness;
- budget exhaustion;
- replay attempts;
- delegation depth;
- conformance version.

Raw signed credentials should never be emitted to telemetry.

---

# 8. Explicitly Out of Scope for Humanist Core 2.0

1. Prompt censor  
2. General content moderation framework  
3. Biological-human detector  
4. Truth detector  
5. Universal moral classifier  
6. IAM replacement  
7. KMS replacement  
8. Service mesh  
9. SIEM  
10. Universal policy language  
11. LLM reasoning monitor  
12. DRM system  
13. General workflow orchestrator

---

# 9. Path to Humanist Core 2.0

## Phase A — Model Validation (Now)

Focus:

- real scenarios;
- false-positive checkpoints;
- false-negative boundaries;
- scope ergonomics;
- action semantics;
- AutonomyBudget calibration;
- Python/Go/TS interoperability;
- developer experience.

**Exit criteria:** core primitives and decision semantics are stable; at least two independent implementations converge on canonical vectors.

## Phase B — Protocol Hardening

- freeze schemas;
- formal verification order;
- stable reason codes;
- negative conformance;
- fuzz/property tests;
- version negotiation;
- cryptographic lifecycle.

## Phase C — Authority Continuity

- AuthorityRoot;
- DelegationGrant;
- mandatory attenuation;
- authority provenance graph;
- delegation depth;
- root traceability;
- revocation propagation.

## Phase D — Semantic Checkpoint 2.0

- provenance-aware M2M detection;
- meaningful checkpoint payload;
- human decision protocol;
- reauthorization;
- bounded resume;
- checkpoint provenance.

## Phase E — Production Enforcement

- anti-bypass profile;
- MCP-native enforcement;
- observability;
- privacy-minimized provenance;
- KMS/HSM integration profile;
- performance/load testing.

## Phase F — 2.0 Release Gate

Humanist Core 2.0 should ship only when:

- the normative spec is frozen;
- mandatory conformance is green;
- Python/Go/TS conform;
- sidecar negative E2E is green;
- threat model is published;
- key rotation/revocation is tested;
- authority root/delegation is tested;
- checkpoint/reauthorization is tested;
- anti-bypass requirements are documented;
- compatibility policy is published;
- the production profile requires no security-critical heuristic.

---

# 10. Humanist Core 2.0 Acceptance Criteria

## Authority
- [ ] Every consequential action has explicit authority.
- [ ] Delegated authority is traceable to a human-governed root.
- [ ] Delegation cannot amplify authority.
- [ ] Revocation propagates according to normative rules.

## Action Binding
- [ ] Deterministic canonical action binding.
- [ ] HTTP and MCP action models are normative.
- [ ] Typed tool semantics are used in the production profile.

## Semantic Checkpoint
- [ ] Meaningful boundary → CHECKPOINT/REAUTHORIZE.
- [ ] Checkpoint explains the semantic/risk change.
- [ ] Human response creates bounded renewed authority.
- [ ] Resume cannot silently widen scope.

## M2M Loop Breaking
- [ ] Uses authority provenance, not hop count alone.
- [ ] Delegation depth is observable.
- [ ] Loss of human authority can force checkpoint.
- [ ] Safe long-running chains can continue.

## Cryptography
- [ ] JCS is normative.
- [ ] Cross-language Ed25519 is tested.
- [ ] Rotation/revocation is tested.
- [ ] No private keys appear in logs/provenance.

## Conformance
- [ ] Python mandatory vectors pass.
- [ ] Go mandatory vectors pass.
- [ ] TypeScript mandatory vectors pass.
- [ ] Sidecar mandatory vectors pass.
- [ ] Differential conformance runs in CI.

## Production
- [ ] Anti-bypass invariant documented.
- [ ] Threat model published.
- [ ] Negative E2E green.
- [ ] Fuzz/property testing exists.
- [ ] Observability is privacy-minimized.

---

# 11. Manifesto Alignment in 2.0

| Manifesto principle | Humanist Core 2.0 mechanism |
|---|---|
| Principle 2 — intent/context | IntentEnvelope + scoped authority |
| Principle 2 — graded response | ALLOW / AUDIT / CHECKPOINT / REAUTHORIZE / DENY |
| Principle 3 — transparent intent | signed intent + provenance |
| Principle 4 — sovereignty | data classes + minimized provenance + explicit scope |
| Principle 7 — human agency | authority continuity |
| Principle 7.1 — Semantic Checkpoint | checkpoint + human reauthorization |
| Principle 7.1 — M2M protection | provenance-aware delegation-chain breaker |

HACP does not claim to implement Principles 5, 6, 8 and 9 as enforcement primitives.

---

# 12. Humanist Core 2.0 Architectural Formula

```text
Human-Governed Authority Root
            ↓
       IntentEnvelope
            ↓
      Scoped Delegation
            ↓
       DecisionToken
            ↓
      Proposed Action
            ↓
    ┌──── HACP Boundary ────┐
    │ signature             │
    │ temporal validity     │
    │ revocation            │
    │ authority lineage     │
    │ action binding        │
    │ scope                 │
    │ semantic boundary     │
    │ autonomy budget       │
    │ replay                │
    └──────────┬────────────┘
               ↓
     ALLOW / CHECKPOINT / DENY
               ↓
       Human reauthorization
       when meaning changes
```

---

# 13. Why Validate the Model Before Technology Completion

Prematurely implementing every production mechanism risks freezing the wrong model too early.

Preferred order:

```text
Model
  ↓
real scenarios
  ↓
interoperability
  ↓
conformance
  ↓
observe failure modes
  ↓
stabilize invariants
  ↓
technology hardening
  ↓
Humanist Core 2.0
```

The project should first demonstrate not only that “the idea appears correct,” but that:

> the model survives independent implementation and real enforcement scenarios.

---

# 14. Conclusion

The current Humanist Core stage should be **model validation**.

Humanist Core 2.0 should be **technological closure**:

- human authority has a provable root;
- machine delegation is attenuated and traceable;
- M2M breaking is provenance-aware;
- Semantic Checkpoint becomes a complete protocol flow;
- action semantics are typed;
- key/revocation lifecycle is defined;
- conformance becomes a release gate;
- negative security scenarios are covered by E2E;
- deployment prevents bypass;
- provenance minimizes content collection;
- versioning and compatibility are formalized.

The 2.0 success criterion can be stated in one sentence:

> **An autonomous system may operate for long periods without continuous human interaction, but it cannot silently expand, delegate, restore, or reinterpret human authority beyond explicitly authorized boundaries.**

That is the engineering meaning of Human Agency Continuity.

---

## References

- Digital Humanism Manifesto: https://github.com/digital-humanism/manifesto
- Humanist Core: https://github.com/digital-humanism/humanist-core
- HACP Architecture v2.0: https://github.com/digital-humanism/humanist-core/blob/main/docs/ARCHITECTURE_v2.0.md
- HACP Sidecar: https://github.com/digital-humanism/hacp-sidecar

---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)