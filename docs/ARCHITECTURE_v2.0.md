# Humanist Core — Architecture v2.0

**Working title:** Human Agency Continuity Protocol (HACP)  
**Reference implementation:** `humanist-core`  
**Architecture version:** v2.0  
**Current verified wire interoperability:** HACP v0.9  
**Implementation status:** active, partially implemented and cross-language verified  
**Last interoperability verification:** 2026-08-15

### Document Status

```text
Humanist Core v0.1
experimental prototype — implemented and tested

HACP / Architecture v2.0
second-generation architecture derived from prototype findings;
reference implementation pending
```

This document describes the **v2.0 target architecture** and the protocol-level invariants that should govern a future reference implementation.

> **Scope principle:** HACP has broad architectural scope, but intentionally narrow implementation ownership. It coordinates authority mechanisms; it does not seek to replace them.

---

## 1. Purpose

Humanist Core v2.0 is designed around a different central question from traditional "human-in-the-loop" systems.

The goal is **not** to prove that a message, confirmation, or interaction was produced by a biological human.

The goal is to establish that:

> **A meaningful autonomous action was consciously authorized by a human, and the autonomous system did not exceed the boundaries of that authorization.**

This changes the object of verification.

Instead of attempting to classify:

```text
HUMAN / NOT HUMAN
```

the architecture evaluates:

```text
Is the proposed action authorized?
        ↓
Is it inside the declared scope?
        ↓
Has the risk materially changed?
        ↓
Has the meaning of the task changed?
        ↓
Is renewed human authority required?
```

Humanist Core v2.0 therefore treats **human agency** as a continuity property of an autonomous process rather than as a one-time proof of human presence.

---

## 2. Foundational Principle

The central architectural invariant is:

> **An autonomous system MAY act without continuous human presence, but MUST NOT cross a meaningful boundary without renewed human authority.**

This distinction is fundamental.

Human presence does not necessarily imply human agency:

```text
AI: Approve?
Human: Yes.
```

A human may technically participate while exercising almost no meaningful judgment.

Conversely, continuous physical presence is not required for agency.

A human can authorize an agent to perform hundreds of safe operations and leave the system unattended, provided those operations remain inside the consciously defined scope.

Therefore:

> **Human Agency ≠ Human Presence**

Humanist Core v2.0 protects the **continuity of human authority**, not continuous human interaction.

---

## 3. Architectural Shift from v0.1

The earlier architecture contains several important ideas:

- intent provenance;
- hash-linked records;
- autonomous hop limits;
- semantic checkpoints;
- cognitive-friction mechanisms;
- behavioral heuristics intended to detect machine-generated participation.

These ideas are retained where useful, but their roles change.

### v0.1 model

```text
Human?
   ↓
yes / no
   ↓
allow / interrupt
```

### v2.0 model

```text
Human Intent
      ↓
Authorization Scope
      ↓
Autonomous Execution
      ↓
Risk / Semantic Change Detection
      ↓
Meaningful Boundary?
   ↙              ↘
 no                yes
 ↓                  ↓
continue      Human Checkpoint
                    ↓
             Renewed Authority
```

The architecture no longer attempts to infer biological humanity from typing speed, reading time, or linguistic patterns.

Those signals may remain as **risk telemetry**, but they are never treated as proof.

---


## 3.1 Evidence from v0.1

Humanist Core v0.1 was not only a conceptual proposal.

A working prototype was implemented and experimentally tested. The prototype demonstrated that several core ideas are technically enforceable in practice:

- human intent can be recorded and linked to later execution;
- autonomous agent chains can be interrupted;
- checkpoints can be inserted into runtime execution;
- behavioral and timing signals can be collected;
- agent execution can resume after explicit human intervention.

The prototype also exposed limitations that directly motivate v2.0.

| v0.1 observation | Limitation exposed | v2.0 architectural response |
|---|---|---|
| Hash-linked intent ledger is technically practical | Hash linkage alone does not establish complete authority provenance | **Provenance Graph + signatures + external anchoring options** |
| Autonomous chain interruption works | Fixed hop count does not represent action risk | **Autonomy Budget + contextual Risk Engine** |
| Human checkpoint can reliably interrupt execution | Confirmation alone does not guarantee meaningful human agency | **Semantic Checkpoint** |
| Timing and cognitive-friction heuristics can flag anomalies | Response time is not proof of biological humanity | **Behavioral telemetry, never identity proof** |
| Semantic similarity can expose repetitive machine-like behavior | Similarity is not equivalent to machine authorship | **Risk signal rather than HUMAN / NOT HUMAN classifier** |
| Human intervention can resume an agent workflow | Generic approval can be too broad or persist too long | **Bounded, expiring Decision Token** |
| Agent execution can be constrained operationally | No formal model existed for legitimate scope evolution | **Intent Envelope + Semantic Delta Guard + Reauthorization** |
| Intent can be logged before autonomous work starts | Logged intent alone does not define a complete capability boundary | **Structured authorization scope** |

The significance of v0.1 is therefore not that every original mechanism should be preserved.

Its significance is that it provided **prototype evidence** for the enforceability of human checkpoints, intent provenance, and runtime interruption, while revealing where binary human-detection and fixed-hop autonomy controls were too weak.

A concise interpretation is:

```text
v0.1
prove that intervention can be enforced
        ↓
observe where the trust model breaks
        ↓
v2.0
replace presence detection
with authority continuity
```

---

## 3.2 Design Lessons Carried Forward

The following lessons from v0.1 are retained as explicit v2.0 design rules.

### Lesson 1 — Detect authority, not biology

The system should not attempt to prove that a text was produced by a biological human.

It should determine whether the proposed action still carries valid human authority.

### Lesson 2 — Interruptions should be consequence-aware

A harmless chain of many read-only operations may remain safely autonomous.

A single irreversible action may require immediate human authority.

### Lesson 3 — Human intervention must have semantics

The system should ask the human to decide **what boundary is intended**, not merely to click a confirmation control.

### Lesson 4 — Approval must be bounded

Human approval should become a narrowly scoped capability, not a persistent boolean state.

### Lesson 5 — Intent may evolve, but authority must be renewed

Legitimate task evolution is allowed.

Silent mandate expansion is not.

---

# 4. High-Level Architecture

```text
                  ┌──────────────────────┐
                  │        HUMAN         │
                  │ intention / decision │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   INTENT ENVELOPE    │
                  │ scope / limits / TTL │
                  │ signature / context  │
                  └──────────┬───────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                     AGENCY KERNEL                        │
│                                                          │
│  Scope Guard ─ Risk Engine ─ Autonomy Budget            │
│       │             │             │                      │
│       └─────────────┼─────────────┘                      │
│                     ▼                                    │
│              Semantic Delta Guard                        │
│                     │                                    │
│                     ▼                                    │
│              Checkpoint Engine                           │
└─────────────────────┬────────────────────────────────────┘
                      │
             ┌────────┴─────────┐
             │                  │
             ▼                  ▼
       continue agent      HUMAN CHECKPOINT
             │                  │
             │             deliberate
             │                  │
             └────────┬─────────┘
                      ▼
              ┌──────────────┐
              │ DECISION     │
              │ TOKEN        │
              └──────┬───────┘
                     │
                     ▼
                  ACTION
                     │
                     ▼
              Provenance Graph
```

The **Agency Kernel** is the core enforcement layer.

It evaluates every meaningful proposed action against:

1. the original human intent;
2. authorization scope;
3. accumulated autonomy;
4. action risk;
5. semantic deviation;
6. current context;
7. provenance history;
8. any previous human decisions.

---

# 5. Intent Envelope

The original human instruction must not be represented merely as a prompt hash.

Humanist Core v2.0 introduces an explicit **Intent Envelope**.

An Intent Envelope represents the space of authority granted by the human.

Example:

```python
IntentEnvelope(
    actor_id="user:key:7F23...",
    objective="analyse_incidents",

    scope={
        "systems": ["ServiceDesk"],
        "operations": [
            "read",
            "classify",
            "summarize"
        ],
        "forbidden": [
            "delete",
            "send_external",
            "modify"
        ]
    },

    constraints={
        "max_records": 10000,
        "max_cost": 5.00,
        "data_export": False
    },

    validity={
        "issued_at": "...",
        "expires_at": "...",
        "single_session": True
    },

    context_digest="sha256(...)",

    signature="ed25519:..."
)
```

The important distinction is that the human does not merely authorize a sentence.

The human authorizes a **bounded capability space**.

Conceptually:

```text
Human
  │
  └── grants capability ──► Agent
                              │
                              ├─ READ       ✓
                              ├─ ANALYZE    ✓
                              ├─ CLASSIFY   ✓
                              │
                              ├─ MODIFY     ✗
                              └─ DELETE     ✗
```

The agent may operate autonomously within this envelope.

Crossing its boundaries requires renewed authority.

---

# 6. Scope Guard

The **Scope Guard** determines whether a proposed action remains within the Intent Envelope.

It evaluates dimensions such as:

```text
operation
resource
system
audience
data class
effect
quantity
privilege
cost
duration
externality
```

Example:

Original scope:

```text
operation = analyse
system    = ServiceDesk
audience  = requester
effect    = informational
```

Proposed action:

```text
operation = publish
system    = email
audience  = management
effect    = reputational
```

Even if both actions are related to the same dataset, the second action is not equivalent to the first.

The Scope Guard therefore does not rely solely on tool names or technical permissions.

It evaluates the **meaning and effect of the action**.

---

# 7. Autonomy Budget

Humanist Core v2.0 replaces a fixed autonomous hop counter with an **Autonomy Budget**.

A simple hop-count rule treats all actions as equivalent:

```text
search → read → parse → summarize
```

may contain four steps but remain low risk.

Meanwhile:

```text
send_email()
```

may be significant on the first autonomous step.

Therefore:

```text
hop_count > N
```

is replaced by:

```text
autonomy_cost > autonomy_budget
```

Illustrative cost model:

```text
read file                  +1
search database            +1
run local calculation      +1
summarize                  +1

modify record              +4
send external message      +6
publish                    +8
spend money               +10
delete                    +10
change permissions        +12
```

These values are policy-defined rather than universal constants.

More generally:

```text
Risk =
    irreversibility
  × externality
  × uncertainty
  × privilege
  × scope_deviation
```

The effective autonomy cost may therefore vary by context.

Example:

```text
read 50,000 service records
        ↓
LOW

produce an analytical conclusion
        ↓
MEDIUM

automatically reclassify SLA status
        ↓
HIGH

send employee-level conclusions
to management
        ↓
CRITICAL
```

The checkpoint is triggered because autonomy has crossed a meaningful risk boundary, not because an arbitrary number of tool calls has occurred.

---

# 8. Semantic Delta Guard

The **Semantic Delta Guard** is one of the central components of v2.0.

Its purpose is to detect when the autonomous system is still technically pursuing the same task while the **meaning, impact, or social effect of the action has changed**.

Example.

Original human intent:

> Analyse service requests and identify potentially problematic cases.

Later autonomous proposal:

> I identified 147 employees who may be violating the process and will automatically send their names to management.

The chain of reasoning may be technically coherent.

But the semantic meaning has changed.

Structured comparison:

```text
DECLARED INTENT
      │
      ▼
CURRENT PROPOSED ACTION
      │
      ▼
SEMANTIC DELTA
```

Instead of relying only on cosine similarity between embeddings, the system compares structured dimensions.

Example:

```text
Intent
────────────────────────────
verb      = analyse
object    = service_requests
effect    = informational
audience  = requester


Action
────────────────────────────
verb      = send
object    = employee_assessment
effect    = reputational
audience  = managers
```

Detected changes:

```text
operation:
analyse → publish

effect:
informational → reputational

audience:
requester → third_party
```

This constitutes a meaningful boundary.

Result:

```text
CHECKPOINT REQUIRED
```

Semantic similarity may be high while semantic authority has changed.

Therefore semantic distance and authorization distance are treated as separate concepts.

---

# 9. Risk Engine

The Risk Engine evaluates the consequence of a proposed action.

Risk is contextual and should consider at minimum:

```text
irreversibility
externality
financial effect
reputational effect
privacy impact
security privilege
legal significance
uncertainty
scope deviation
data sensitivity
blast radius
```

The result is not necessarily a single universal score.

An implementation may return:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

or a numeric internal value.

The Risk Engine influences:

- autonomy budget consumption;
- required agency level;
- checkpoint type;
- token lifetime;
- audit requirements;
- whether an action is denied entirely.

---

# 10. Semantic Checkpoints

A Humanist checkpoint must require **human judgment**, not merely human interaction.

The purpose is not to prove biological presence.

The purpose is to require the human to actively define or confirm the meaning of the action.

## Weak checkpoint

```text
Delete 18,432 records?

[ YES ]
```

This creates almost no cognitive friction.

## Slightly stronger but still weak

```text
Type DELETE to continue.
```

The human performs an action but may still avoid meaningful deliberation.

## Humanist semantic checkpoint

```text
Proposed action
────────────────────────────────
Delete: 18,432 records
System: production
Reversible: no

Reason:
Records classified as expired.

Changed since original intent:
Original request requested analysis only.
Deletion was not explicitly authorized.

Required human decision:
Choose the intended boundary.

○ Analyse only
○ Generate deletion proposal
○ Delete selected records
```

This checkpoint forces a decision about **scope and meaning**.

The architecture therefore defines:

> **Semantic friction is more valuable than mechanical friction.**

---

# 11. Checkpoint vs Reauthorization

Humanist Core v2.0 distinguishes two fundamentally different situations.

## CHECKPOINT

The action is broadly related to the authorized task, but requires a meaningful human decision.

Example:

```text
Analysis discovered two competing interpretations.
Select which interpretation governs the next step.
```

## REAUTHORIZE

The proposed action falls outside the authority contained in the original Intent Envelope.

Example:

```text
Original authority:
analyse incidents

Proposed action:
send employee-level findings to management
```

This does not require merely another confirmation.

It requires a new or expanded authorization scope.

Therefore:

```text
CHECKPOINT ≠ REAUTHORIZE
```

This distinction prevents a chain of small approvals from silently expanding into unlimited authority.

---

# 12. Decision Token

A human checkpoint must not produce a global flag such as:

```python
human_confirmed = True
```

Such a state is ambiguous and dangerous.

Instead the checkpoint produces a narrowly scoped, short-lived **Decision Token**.

Example:

```python
DecisionToken(
    permits="delete",
    resource="dataset:expired_records",
    selector_hash="...",
    max_items=18432,
    expires_in=300,
    nonce="...",
    parent_intent="...",
    signature="..."
)
```

Conceptually:

```text
Human decision
      │
      ▼
short-lived capability
      │
      ▼
one bounded action
```

A Decision Token should bind, where appropriate:

```text
actor
operation
resource
selector
quantity
context
time window
parent intent
checkpoint
policy version
nonce
```

The token should not represent generic future permission.

It should authorize a specific decision under specific conditions.

---

# 13. Agency Kernel

The Agency Kernel combines the core authorization logic.

Illustrative interface:

```python
decision = agency.evaluate(
    intent=current_intent,
    proposed_action=action,
    context=context,
    provenance=history
)

match decision:

    case ALLOW:
        execute()

    case ALLOW_WITH_AUDIT:
        log()
        execute()

    case CHECKPOINT:
        request_human_decision()

    case REAUTHORIZE:
        request_new_intent_scope()

    case DENY:
        stop()
```

Possible outcomes:

### ALLOW

The action is low risk and fully within current authority.

### ALLOW_WITH_AUDIT

The action remains authorized but requires stronger provenance.

### CHECKPOINT

A meaningful human judgment is required.

### REAUTHORIZE

The action exceeds the current Intent Envelope.

### DENY

The action violates policy, security rules, or a non-overridable constraint.

---

# 14. Provenance Graph

A simple local hash-chain is useful for detecting modification of individual records, but a stronger architecture needs explicit causal provenance.

Humanist Core v2.0 therefore models provenance as a directed graph.

```text
                     Human Intent
                         │
             ┌───────────┴────────────┐
             ▼                        ▼
        Agent Plan               Policy Version
             │
             ▼
         Tool Call
             │
             ▼
         Tool Result
             │
             ▼
       Semantic Delta
             │
             ▼
      Human Decision
             │
             ▼
       Decision Token
             │
             ▼
          Action
```

Each event can be represented as:

```python
{
    "event_id": "...",
    "type": "action",
    "parents": [...],

    "payload_digest": "...",
    "policy_digest": "...",

    "actor": "...",
    "timestamp": "...",

    "signature": "..."
}
```

This makes it possible to answer:

> Why was action X allowed?

By walking backwards:

```text
ACTION
  ↓
Decision Token
  ↓
Human Decision
  ↓
Checkpoint
  ↓
Semantic Delta
  ↓
Agent Plan
  ↓
Original Intent
```

This provides causal auditability rather than simple chronological logging.

---

# 15. Cryptographic Provenance

Hashing alone does not establish complete provenance.

A robust implementation should progressively support:

```text
digital signatures
key ownership
external timestamps
append-only storage
remote anchoring
policy digests
nonce protection
token expiration
chain / DAG verification
```

Possible mechanisms include:

- Ed25519 signatures;
- TPM-backed or platform-backed keys;
- hardware security modules;
- append-only transparency logs;
- external timestamp authorities;
- Merkle roots periodically anchored outside the local runtime.

The goal is not merely to prove that a record has a hash.

The goal is to establish:

```text
who authorized
what was authorized
under which policy
for which context
at what time
and which action resulted
```

---

# 16. Behavioral and Cognitive Signals

Cognitive and behavioral heuristics are not removed entirely.

They are reclassified.

Signals such as:

```text
abnormal response velocity
repetitive approvals
copy/paste patterns
impossible throughput
mass-identical decisions
automation signatures
highly repetitive semantic structure
```

may provide useful evidence that a checkpoint is being mechanically bypassed.

However:

> **These signals MUST NOT be treated as proof that a participant is or is not human.**

Their role is:

```text
Behavioral Signal
       ↓
Risk Adjustment
       ↓
Possible stronger checkpoint
```

For example:

```python
risk += behavioral_anomaly_score
```

but never:

```python
if elapsed < minimum_reading_time:
    raise NotHuman()
```

Timing and linguistic patterns are therefore **telemetry**, not identity.

---

# 17. Human Agency Assurance Levels

Humanist Core v2.0 defines progressively stronger levels of agency assurance.

| Level | Description |
|---|---|
| **A0** | Autonomous machine action without human provenance |
| **A1** | Action derived from a recorded human intent |
| **A2** | Action occurs inside a cryptographically bounded authorization scope |
| **A3** | A meaningful semantic change has passed a human checkpoint |
| **A4** | A specific high-impact or irreversible action is backed by a fresh Decision Token |

Example policy:

```text
information search             A1
local analysis                 A1
database read                  A2
record modification            A2 / A3
external publication           A3
production deletion            A4
financial transaction          A4
privilege escalation           A4
```

This enables a system to define:

```text
required_agency_level(action)
```

rather than relying on a universal "human present" flag.

---

# 18. Meaningful Boundaries

A **meaningful boundary** is any change that materially alters the authority, consequence, audience, reversibility, or purpose of an autonomous action.

Typical boundary dimensions include:

```text
read → write
analysis → action
internal → external
draft → publish
private → shared
reversible → irreversible
informational → reputational
local → production
no-cost → financial commitment
user-only → third party
low privilege → elevated privilege
known scope → new resource
```

Crossing such a boundary may require:

```text
CHECKPOINT
```

or:

```text
REAUTHORIZE
```

depending on whether the action remains inside the original mandate.

---

# 19. Example End-to-End Flow

Human instruction:

> Analyse Service Desk incidents and identify recurring technical patterns.

## Step 1 — Intent Envelope

```text
objective:
identify recurring technical patterns

allowed:
read
analyse
classify
summarize

forbidden:
modify records
notify employees
publish externally
```

Agency level:

```text
A2
```

## Step 2 — Autonomous analysis

Agent performs:

```text
read dataset
normalize text
cluster incidents
calculate recurrence
generate technical categories
```

All actions remain within scope.

Result:

```text
ALLOW
```

## Step 3 — Semantic shift

Agent proposes:

> Automatically assign the newly detected category to every matching Service Desk record.

Structured delta:

```text
analysis → modification
informational → operational
read-only → write
```

Result:

```text
REAUTHORIZE
```

## Step 4 — Human decision

Checkpoint explains:

```text
Original authority:
analysis only

Proposed new action:
modify 7,412 Service Desk records

Impact:
operational

Reversible:
yes, but affects production data
```

Human selects:

```text
Generate proposed changes only.
Do not write them.
```

## Step 5 — Decision Token

A token authorizes:

```text
operation:
generate_change_set

resource:
7,412 selected records

write:
false

TTL:
10 minutes
```

## Step 6 — Provenance

The resulting proposal is connected to:

```text
original intent
analysis
semantic delta
checkpoint
human decision
decision token
generated change set
```

The agent never obtained permission to modify production records.

Human agency remained continuous.

---

# 20. Failure Modes Addressed by v2.0

## Confirmation fatigue

Repeated `[Yes]` prompts become mechanical.

**Mitigation:** semantic checkpoints require meaningful choices.

---

## Agent mandate expansion

An agent gradually turns an analytical task into an operational action.

**Mitigation:** Semantic Delta Guard + reauthorization.

---

## Arbitrary hop limits

Safe multi-step chains are interrupted while dangerous single-step actions are allowed.

**Mitigation:** Autonomy Budget + contextual Risk Engine.

---

## Global approval state

A past approval is reused for future unrelated actions.

**Mitigation:** narrow, expiring Decision Tokens.

---

## False proof of humanity

Typing speed or text structure is interpreted as biological identity.

**Mitigation:** behavioral signals are risk telemetry only.

---

## Weak provenance

A chronological log records what happened but not why an action was authorized.

**Mitigation:** causal Provenance Graph.

---

## Scope ambiguity

A natural-language prompt is treated as unlimited authority.

**Mitigation:** explicit Intent Envelope.

---

# 21. Security Invariants

A conforming implementation should preserve the following invariants.

### Invariant 1 — No silent scope expansion

An agent MUST NOT silently extend its authority beyond the Intent Envelope.

### Invariant 2 — High-impact actions require explicit authority

Irreversible or high-impact actions MUST meet the policy-defined Agency Assurance Level.

### Invariant 3 — Approval is bounded

Human approval MUST be scoped to a defined action or capability.

### Invariant 4 — Approval expires

Decision authority MUST NOT remain valid indefinitely unless explicitly designed to do so.

### Invariant 5 — Provenance is causal

The system SHOULD be able to reconstruct why a consequential action was allowed.

### Invariant 6 — Behavioral inference is non-authoritative

Behavioral or cognitive heuristics MUST NOT independently establish human identity or authority.

### Invariant 7 — Semantic change is security-relevant

A change in purpose, audience, effect, privilege, or reversibility MUST be considered during authorization.

### Invariant 8 — Presence is insufficient

The existence of a human interaction MUST NOT automatically imply meaningful human control.

---

# 22. Conceptual API

A possible developer-facing API could look like:

```python
from humanist_core import AgencyKernel

agency = AgencyKernel(policy="agency-policy.yaml")

intent = agency.authorize_intent(
    objective="analyse incidents",
    scope={
        "operations": ["read", "analyse", "classify"],
        "systems": ["ServiceDesk"]
    }
)

action = ProposedAction(
    operation="publish",
    resource="incident_analysis",
    audience="management",
    effect="reputational"
)

decision = agency.evaluate(
    intent=intent,
    proposed_action=action,
    context=context
)

if decision.requires_checkpoint:
    token = agency.checkpoint(decision)

    if token:
        agency.execute(action, token=token)
```

The implementation details may vary, but the architectural boundary remains the same:

> execution depends on **authority**, not merely agent intention.

---

# 23. Policy Layer

Risk values, meaningful boundaries, required agency levels, and token rules should be policy-controlled rather than hard-coded.

Example:

```yaml
operations:

  read:
    risk: low
    agency_level: A1

  modify:
    risk: high
    agency_level: A3

  delete:
    risk: critical
    agency_level: A4
    decision_token:
      ttl_seconds: 300

boundaries:

  - from: read
    to: write
    action: checkpoint

  - from: internal
    to: external
    action: reauthorize

  - from: reversible
    to: irreversible
    action: reauthorize
```

This allows Humanist Core to operate across different domains without pretending that one universal risk model applies everywhere.

---

# 24. Humanist Core v2.0 Component Model

Proposed modules:

```text
humanist_core/
│
├── agency/
│   ├── kernel.py
│   ├── decisions.py
│   └── assurance.py
│
├── intent/
│   ├── envelope.py
│   ├── signer.py
│   └── scope.py
│
├── guards/
│   ├── scope_guard.py
│   ├── semantic_delta.py
│   └── autonomy_budget.py
│
├── risk/
│   ├── engine.py
│   ├── policy.py
│   └── behavioral_signals.py
│
├── checkpoint/
│   ├── engine.py
│   ├── semantic_checkpoint.py
│   └── reauthorization.py
│
├── tokens/
│   ├── decision_token.py
│   ├── verifier.py
│   └── expiration.py
│
├── provenance/
│   ├── graph.py
│   ├── event.py
│   ├── signer.py
│   └── verifier.py
│
└── integrations/
    ├── langchain.py
    ├── agents.py
    └── middleware.py
```

The exact package layout is implementation-specific.

The architectural separation is more important than the directory names.

---


## 24.1 Architecture Scope vs Implementation Ownership

HACP intentionally spans several security and governance concerns:

```text
intent
authorization
runtime policy
semantic boundaries
risk
human checkpoints
decision capabilities
provenance
```

This broad architectural scope does **not** imply that the Humanist Core implementation should reimplement every underlying mechanism.

The preferred layering is:

```text
┌──────────────────────────────────────────────┐
│                    HACP                      │
│ authority continuity / boundary semantics   │
├──────────────────────────────────────────────┤
│           Humanist Core runtime              │
│ Agency Kernel / Guards / Tokens / Graph      │
├──────────────────────────────────────────────┤
│      Existing infrastructure substrates      │
│ OAuth / IAM / OPA / KMS / signatures / DB   │
├──────────────────────────────────────────────┤
│        Agent and application runtimes        │
│ LangChain / custom agents / MCP / services   │
└──────────────────────────────────────────────┘
```

The governing principle is:

> **HACP coordinates authority mechanisms; it does not seek to replace them.**

Examples:

| Concern | HACP responsibility | Prefer existing infrastructure |
|---|---|---|
| Identity | bind authority to an actor | IAM / workload identity |
| Credentials | define semantic scope and renewal | OAuth / capability credentials |
| Policy evaluation | define HACP-specific policy inputs and outcomes | OPA / Cedar / equivalent policy engines |
| Cryptographic signing | define what must be signed | KMS / TPM / HSM / standard crypto libraries |
| Storage | define provenance semantics | append-only or durable storage systems |
| Agent runtime | enforce HACP decisions at execution boundaries | framework-specific middleware |
| Semantic analysis | define required comparison dimensions | interchangeable model / rules engine |

This separation is critical.

A broad protocol with narrow implementation ownership is composable.

A monolithic framework that attempts to replace identity, authorization, cryptography, policy, provenance, and agent execution simultaneously is not.

---

# 25. Design Philosophy

Humanist Core v2.0 does not treat autonomy itself as the enemy.

Autonomous systems can execute large amounts of useful work without continuously interrupting the human.

The problem arises when delegated execution becomes **delegated authority without an explicit boundary**.

Therefore the design goal is not:

> Keep the human clicking.

It is:

> Keep autonomous action causally connected to human authority.

This permits efficient autonomy while protecting meaningful human control.

---

# 26. Core Definitions

## Human Intent

A human-originated objective together with context and constraints.

## Intent Envelope

A bounded representation of the authority granted to an autonomous system.

## Agency

The ability of the human to determine the meaningful direction and boundaries of autonomous action.

## Agency Continuity

The property that every consequential autonomous action remains connected to valid human authority.

## Semantic Delta

A meaningful difference between the authorized purpose and a proposed autonomous action.

## Meaningful Boundary

A transition that materially changes purpose, effect, audience, privilege, reversibility, resource scope, or risk.

## Semantic Checkpoint

A human interaction requiring judgment about the meaning or boundary of an action.

## Reauthorization

The creation or expansion of authority when an action falls outside the existing Intent Envelope.

## Decision Token

A bounded cryptographic capability produced by a human decision and valid only for a defined action or scope.

## Provenance Graph

A causal record linking intent, reasoning, tools, decisions, authorization, and action.

---

# 27. Human Agency Continuity Protocol

The architecture can ultimately be expressed as a protocol invariant:

```text
INTENT
  ↓
AUTHORITY
  ↓
AUTONOMY
  ↓
BOUNDARY DETECTION
  ↓
HUMAN DECISION
  ↓
RENEWED AUTHORITY
  ↓
ACTION
```

The essential rule is:

> **No meaningful autonomous transition without sufficient human authority.**

This creates a continuous chain:

```text
Human Intent
    │
    ▼
Authorized Autonomy
    │
    ▼
Meaningful Boundary
    │
    ▼
Human Judgment
    │
    ▼
Renewed Authority
    │
    ▼
Authorized Autonomy
```

Human authority therefore behaves not as a permanent boolean flag, but as a renewable and bounded capability.

---


## 27.1 Suggested v2.0 Reference-Implementation Sequence

The v2.0 architecture can be implemented incrementally without attempting the entire protocol surface at once.

### Phase 1 — Authority Core

Implement:

```text
IntentEnvelope
ScopeGuard
AgencyDecision
DecisionToken
```

Goal:

> Establish explicit bounded authority and eliminate global approval state.

### Phase 2 — Boundary Detection

Implement:

```text
SemanticDeltaGuard
RiskEngine
AutonomyBudget
CHECKPOINT / REAUTHORIZE distinction
```

Goal:

> Detect when inherited authority is no longer sufficient.

### Phase 3 — Provenance

Implement:

```text
ProvenanceGraph
signed events
policy digests
token verification
```

Goal:

> Make consequential actions causally explainable and verifiable.

### Phase 4 — Runtime Integrations

Add adapters for selected agent frameworks and tool runtimes.

Goal:

> Enforce the protocol at real execution boundaries while keeping the core framework-independent.

### Phase 5 — Evaluation

Evaluate at minimum:

- false-positive checkpoint rate;
- missed meaningful boundaries;
- approval fatigue;
- semantic-delta precision;
- token misuse resistance;
- provenance completeness;
- policy portability;
- runtime overhead.

The evaluation objective is not merely to show that checkpoints occur.

It is to test whether the system preserves **human authority with the minimum necessary interruption of useful autonomy**.

---

# 28. Final Architectural Principle

Humanist Core v2.0 is not an AI detector.

It is not a biological-human detector.

It is not primarily a confirmation framework.

It is not designed to prevent machines from operating autonomously.

Its purpose is narrower and more fundamental:

> **to prevent delegated machine execution from silently becoming independent machine authority.**

A human may delegate execution.

A human may delegate analysis.

A human may delegate large areas of operational freedom.

But an autonomous system must not transform that delegation into a mandate that the human never gave.

Therefore the final principle of the architecture is:

> **The machine may carry the action.  
> The human retains the mandate.**

---


# 29. Related Work and Positioning

Humanist Core v2.0 does not emerge in isolation.

Recent work on agent authorization, autonomy governance, intent binding, and reasoning provenance addresses several parts of the same problem space. HACP should therefore be understood as a synthesis and architectural position within this developing field, rather than as a claim that scoped authority, human checkpoints, or provenance are individually novel concepts.

The closest related approaches identified at the time of this document are summarized below.

## 29.0 Comparative Landscape

The following matrix is intended as a rapid architectural orientation rather than a ranking.

Legend:

```text
✓   explicit / central capability
◐   partial, adjacent, or implementation-dependent
—   not a primary focus of the approach
```

| Architectural capability | CAAM | AgentBound | Safin–Balta | AAL / ACL | IGAC | Reasoning Provenance | **HACP** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Human-originated intent as an authorization input | ✓ | ✓ | ◐ | ◐ | ✓ | ✓ | **✓** |
| Scoped / bounded agent authority | ✓ | ✓ | ◐ | ✓ | ✓ | ◐ | **✓** |
| Multi-hop delegation control | ✓ | ✓ | ◐ | — | ◐ | ✓ | **✓** |
| Intent binding across agent/tool execution | ✓ | ✓ | ◐ | ◐ | ✓ | ◐ | **✓** |
| Runtime authorization before consequential action | ✓ | ✓ | ✓ | ✓ | ✓ | — | **✓** |
| Capability separated from permission / authority | ✓ | ✓ | ✓ | ✓ | ✓ | ◐ | **✓** |
| Risk-sensitive autonomy | ◐ | ✓ | ✓ | ✓ | ◐ | — | **✓** |
| Human approval / escalation checkpoints | ◐ | ✓ | ✓ | ✓ | ◐ | — | **✓** |
| Semantic change / intent-drift detection | ✓ | ◐ | ◐ | ◐ | ✓ | ◐ | **✓** |
| Meaningful boundary as a first-class security event | ◐ | ◐ | ◐ | ◐ | ◐ | — | **✓** |
| Distinction between checkpoint and reauthorization | — | ◐ | ◐ | — | — | — | **✓** |
| Human approval represented as bounded capability/token | ◐ | ◐ | — | — | ◐ | — | **✓** |
| Causal reasoning provenance | — | ◐ | ◐ | — | — | ✓ | **✓** |
| Causal authority provenance | ✓ | ✓ | ◐ | ◐ | ✓ | ◐ | **✓** |
| Explicit authority renewal after semantic boundary | — | — | ◐ | — | — | — | **✓** |
| Human-authority continuity as the primary invariant | — | — | — | — | — | — | **✓** |

### Reading the matrix

The table shows substantial overlap between HACP and existing work.

That overlap is expected and desirable.

HACP is not positioned as a replacement for these approaches:

```text
CAAM                    → delegation and multi-hop intent binding
AgentBound              → runtime behavioral governance
Safin–Balta             → agency/autonomy architecture and escalation
AAL / ACL               → capability vs allowed autonomy
IGAC                    → intent-governed tool authorization
Reasoning Provenance    → causal reasoning traceability
```

The differentiating column appears primarily in the lower part of the matrix.

HACP treats the following sequence as a first-class protocol operation:

```text
valid inherited authority
        ↓
meaningful semantic boundary
        ↓
authority stops propagating
        ↓
human judgment
        ↓
renewed bounded authority
        ↓
autonomous execution continues
```

This is the architectural meaning of **Human Agency Continuity**.

> **Important:** this comparison is a positioning aid, not a claim of exhaustive feature absence in other systems. A `—` means that the capability was not identified as a primary architectural focus in the reviewed material. The landscape is evolving rapidly, and the matrix should be revised as related work develops.

---

## 29.1 Contextual Agent Authorization Mesh (CAAM)

**Contextual Agent Authorization Mesh (CAAM)** is an IETF Internet-Draft focused on runtime authorization for autonomous agents after discovery and delegation.

A particularly relevant concept is **multi-hop intent binding**: maintaining authorization semantics across chains in which one agent delegates work to another agent, service, or tool.

Conceptually:

```text
Human Intent
      ↓
Agent A
      ↓
Agent B
      ↓
Agent C
      ↓
Action
```

The authorization system must determine whether the eventual action still remains inside the semantic boundaries of the original authority.

This is closely related to HACP's concern with authority continuity.

### Relationship to HACP

CAAM primarily asks:

> Does delegated authority remain valid as intent propagates across agent hops?

HACP asks an additional question:

> What happens when the task itself legitimately evolves beyond the semantic boundary of the original authority?

HACP therefore introduces an explicit renewal loop:

```text
Original Intent
      ↓
Authorized Autonomy
      ↓
Meaningful Semantic Change
      ↓
Human Judgment
      ↓
Renewed Authority
      ↓
Continued Autonomy
```

The distinction is important.

HACP does not assume that intent must remain permanently unchanged.

Instead, it requires that **material changes of authority return to the human principal**.

**Reference:** IETF Internet-Draft, *Contextual Agent Authorization Mesh (CAAM)*, draft-barney-caam-00.

---

## 29.2 AgentBound — Verifiable Behavioral Governance

**AgentBound** proposes a runtime governance layer for autonomous agents performing consequential actions.

Its decision model combines three independent authorities:

```text
delegated authorization
        +
owner-signed behavioral constitution
        +
site action contract
        ↓
permit / review / deny
```

AgentBound also introduces cryptographically verifiable governance receipts that bind actions to the delegation, policies, and semantic artifacts governing the decision.

This is strongly related to several HACP components:

```text
AgentBound                     HACP
────────────────────────────────────────────
runtime governance        →   Agency Kernel
delegated authorization   →   Intent Envelope
action contracts          →   Policy Layer
governance receipts       →   Provenance Graph
bounded delegation        →   bounded authority
review decision           →   Checkpoint
```

### Relationship to HACP

AgentBound is one of the closest architectural relatives of HACP.

Its primary emphasis is **verifiable behavioral governance before execution**.

HACP places its primary invariant one level higher:

> Autonomous execution must remain continuously connected to human authority, and a meaningful boundary invalidates inherited authority until that authority is renewed.

The difference is therefore primarily one of architectural center of gravity.

AgentBound centers governance composition.

HACP centers **continuity and renewal of human mandate**.

**Reference:** Anuj Kaul, Qianlong Lan, Pranay Gupta, *AgentBound: Verifiable Behavioral Governance for Autonomous AI Agents*, arXiv:2606.30970, 2026.

---

## 29.3 Autonomy and Agency in Agentic AI

Safin and Balta distinguish two related but separate design dimensions:

```text
Agency
= what the system can do

Autonomy
= how far it can act without human involvement
```

Their framework connects increasing action consequence with architectural tactics such as:

- checkpoints;
- escalation;
- multi-agent delegation;
- tool provisioning;
- tool fencing;
- write staging.

The work also emphasizes responsibility, reversibility, and auditability.

This is closely aligned with the motivation behind the HACP **Autonomy Budget** and **Risk Engine**.

### Relationship to HACP

The Safin–Balta model provides a useful design space for reasoning about how much autonomy should accompany different kinds of agency.

HACP adds a runtime authorization invariant:

```text
capability
        ≠
current authority
```

and models renewed human authority as an explicit transition in the execution protocol.

In other words:

```text
Safin–Balta:
Where should the system sit
in agency/autonomy space?

HACP:
What authority allows the system
to remain there during this execution,
and when must that authority be renewed?
```

**Reference:** Damir Safin, Dian Balta, *Autonomy and Agency in Agentic AI: Architectural Tactics for Regulated Contexts*, arXiv:2605.12105, 2026.

---

## 29.4 Allowed Autonomy Levels vs Autonomous Capability Levels

Zheng et al. explicitly separate:

```text
ACL — Autonomous Capability Level
what the system is technically able to do

AAL — Allowed Autonomy Level
what the system is permitted to do
```

This distinction strongly supports a core HACP principle:

> **Capability does not imply authority.**

A technically capable system can deliberately be constrained to a lower allowed level based on:

- risk;
- reversibility;
- oversight;
- accountability;
- organizational readiness.

### Relationship to HACP

HACP adopts the same conceptual separation but focuses on authorization continuity during execution.

The important distinction becomes:

```text
System capability
      ↓
Policy allowance
      ↓
Human-granted authority
      ↓
Current contextual authority
      ↓
Proposed action
```

A system may therefore be:

```text
technically capable
        AND
organizationally permitted in general
        BUT
not authorized by this human intent
for this action
```

That final layer is central to HACP.

**Reference:** Haining Zheng, Qian Dong, Rodolfo K. Depena, Jonathan D. Bhatia, Feng Xiao, Peng Xu, *Separating Capability from Permission: A Governance Framework for Agentic AI Autonomy Levels*, arXiv:2607.23438, 2026.

---

## 29.5 Intent-Governed Access Control (IGAC)

**Intent-Governed Access Control (IGAC)** addresses a central weakness in conventional agent authorization:

> A credential may permit a tool call even when the user's current request does not justify that call.

IGAC introduces:

- intent certificates;
- session-scoped policy narrowing;
- intent-aware tool manifest filtering;
- intent/tool/payload consistency checks.

Its central invariant is monotonic:

```text
User intent may narrow authority
granted by static integration policy,

but may not expand it.
```

This is closely related to the HACP `Intent Envelope` and `Scope Guard`.

### Relationship to HACP

IGAC and HACP share an important foundation:

```text
credential authority
        ≠
user-intent authority
```

IGAC protects tool execution by binding it to the user's expressed intent.

HACP extends the model beyond intent consistency to **authority renewal**.

A material semantic change may be legitimate.

For example:

```text
initial intent:
analyse records

later desired action:
modify records
```

Under HACP, this transition is not automatically forbidden.

Instead:

```text
semantic boundary detected
        ↓
old authority stops propagating
        ↓
human is asked to decide
        ↓
new Intent Envelope or Decision Token
        ↓
execution may continue
```

Thus HACP treats human intent not only as a narrowing constraint, but as a **renewable source of authority**.

**Reference:** Genliang Zhu, Chu Wang, *Intent-Governed Tool Authorization for AI Agents*, arXiv:2606.22916, 2026.

---

## 29.6 Reasoning Provenance for Autonomous AI Agents

Vispute and Kadam propose the **Agent Execution Record (AER)**, a structured provenance primitive intended to record not only execution state, but why an agent chose an action, what it inferred from observations, how plans changed, and which evidence supported the final result.

Important first-class elements include:

```text
intent
observation
inference
plan revision
evidence
verdict
delegation authority
```

This is strongly related to the HACP `Provenance Graph`.

### Relationship to HACP

Reasoning Provenance primarily addresses:

> How can we reconstruct and analyze the reasoning path that produced an action or conclusion?

HACP asks:

> How can we reconstruct the causal authority path that made a consequential action legitimate?

These are complementary.

A HACP implementation can incorporate AER-like reasoning records inside a broader authorization graph:

```text
Human Intent
      ↓
Authorization
      ↓
Agent Plan
      ↓
Observation / Inference
      ↓
Semantic Delta
      ↓
Human Decision
      ↓
Decision Token
      ↓
Action
```

The distinction is:

```text
reasoning provenance
        +
authority provenance
        =
stronger causal accountability
```

**Reference:** Neelmani Vispute, Aditya Kadam, *Reasoning Provenance for Autonomous AI Agents: Structured Behavioral Analytics Beyond State Checkpoints and Execution Traces*, arXiv:2603.21692, 2026.

---

## 29.7 Authenticated Delegation and Authorization Propagation

Earlier and parallel work also addresses authenticated delegation of human authority to AI agents and the propagation of authorization through multi-agent workflows.

These approaches establish an important foundation:

```text
human principal
      ↓
delegated authority
      ↓
agent identity
      ↓
authorized resources
```

HACP assumes that secure identity and delegation mechanisms may exist underneath the protocol.

It does not attempt to replace OAuth, capability systems, workload identity, delegated credentials, or other authorization substrates.

Instead, HACP operates at the layer where a technically valid delegation must still be interpreted against:

```text
human intent
current context
semantic effect
risk
meaningful boundaries
```

Thus HACP should be considered complementary to lower-level identity and delegation infrastructure.

---

# 30. Positioning of HACP

The individual mechanisms used by HACP are not claimed to be independently novel.

Existing work already provides strong approaches to:

| Problem | Existing work |
|---|---|
| Scoped agent authorization | Authenticated Delegation, IGAC, AgentBound |
| Multi-hop intent binding | CAAM |
| Capability vs permission separation | AAL / ACL |
| Risk-sensitive autonomy | Safin–Balta, AAL / ACL |
| Human approval gates | multiple agent governance systems |
| Runtime policy enforcement | AgentBound, IGAC |
| Reasoning provenance | AER / Reasoning Provenance |
| Cryptographic audit artifacts | AgentBound and related authorization systems |

HACP's proposed contribution is the way these concerns are organized around a single invariant:

> **Human authority must remain continuous across autonomous execution, and inherited authority must stop at a meaningful boundary until the human principal renews it.**

This produces several architectural distinctions that are central to HACP.

---

## 30.1 Intent is not immutable

HACP does not require an autonomous process to remain semantically frozen inside the exact initial request.

Real work evolves.

New facts appear.

The human may legitimately change direction.

Therefore:

```text
semantic drift
        ≠
automatic violation
```

Instead:

```text
meaningful semantic delta
        ↓
authority discontinuity
        ↓
human decision
        ↓
renewed authority
```

The security objective is not to eliminate change.

It is to prevent **silent authority inheritance across that change**.

---

## 30.2 Human approval is not global state

A checkpoint does not produce:

```text
human_confirmed = True
```

It produces a bounded authorization artifact:

```text
Decision Token
```

The token is tied to a particular:

- action;
- resource;
- context;
- limit;
- time window;
- policy;
- parent intent.

Human approval therefore becomes a capability rather than a UI event.

---

## 30.3 Checkpoint and reauthorization are different operations

HACP distinguishes:

```text
CHECKPOINT
```

from:

```text
REAUTHORIZE
```

A checkpoint resolves a meaningful decision inside broadly existing authority.

Reauthorization creates or expands authority when the system has reached the boundary of the existing mandate.

This prevents repeated local confirmations from silently accumulating into global permission.

---

## 30.4 Meaningful boundaries are first-class security objects

Traditional access control often focuses on resources and operations.

HACP additionally treats transitions such as:

```text
analysis → action
internal → external
draft → publish
read → write
informational → reputational
reversible → irreversible
user-only → third-party impact
```

as authorization-relevant events.

The boundary itself is therefore part of the security model.

---

## 30.5 Human authority is renewable

The most distinctive HACP abstraction is:

```text
authority is not permanent
authority is not binary
authority is not inferred from presence

authority is bounded
authority is contextual
authority is renewable
```

This produces the Human Agency Continuity loop:

```text
Human Intent
      ↓
Bounded Authority
      ↓
Autonomous Execution
      ↓
Meaningful Boundary
      ↓
Human Judgment
      ↓
Renewed Authority
      ↓
Autonomous Execution
```

---

# 31. Position Statement

Humanist Core v2.0 / HACP should therefore not be presented as an alternative to existing authorization, agent governance, or provenance frameworks.

It is better understood as an architectural layer that connects them around a human-agency invariant.

In concise form:

```text
CAAM
preserves intent across delegation

IGAC
binds tool authority to expressed intent

AgentBound
governs actions at runtime

AAL / ACL
separates capability from allowed autonomy

Safin–Balta
relates agency, autonomy, consequence and oversight

Reasoning Provenance
records why autonomous reasoning produced an outcome

HACP
asks when inherited human authority
must stop and be renewed
```

The distinguishing question is therefore not:

> Was a human somewhere in the loop?

Nor merely:

> Was this action technically authorized?

Nor only:

> Is this action consistent with the original intent?

The HACP question is:

> **Does this action still carry valid human authority — and if the meaning has materially changed, where was that authority renewed?**

That is the architectural position of Human Agency Continuity Protocol.

---

## 31.1 Non-Novelty Statement

HACP explicitly does **not** claim novelty for the individual concepts of:

- least privilege;
- scoped authorization;
- delegated credentials;
- capability security;
- human approval;
- risk-based escalation;
- intent binding;
- cryptographic provenance;
- autonomous-agent audit logs;
- semantic comparison;
- execution policy enforcement.

The proposed novelty, if validated by further research and comparison, lies in treating **continuity and renewal of human authority across meaningful semantic boundaries** as the primary architectural invariant that organizes these mechanisms into one protocol.

This claim should remain provisional until broader literature review, formalization, and peer review establish whether an equivalent invariant has already been proposed elsewhere.


## Document Status

```text
Humanist Core v0.1
experimental prototype — implemented, tested, and retained as historical context

HACP / Architecture v2.0
second-generation architecture derived from prototype findings

Implemented in humanist-core:
- Authority Core
- Semantic Boundary / Risk Engine
- Cryptographic Provenance
- LangChain runtime integration
- Evaluation framework
- Python HACP SDK

Cross-language interoperability verified:
- Python IntentEnvelope → Go hacp-sidecar
- Python DecisionToken → Go hacp-sidecar
- JCS canonicalization
- Ed25519 signatures
- HTTP ProposedAction / action_hash binding
- real signed request → ALLOW
- token max_uses / replay enforcement

Full Architecture v2.0 reference implementation:
in progress
```

This document describes the **v2.0 target architecture and its protocol-level invariants**, while also distinguishing which parts are already implemented and experimentally verified.

The current Python SDK and Go sidecar interoperate using the HACP v0.9 wire contract. The architecture version (`v2.0`) and the wire-protocol version (`v0.9`) are separate version dimensions and should not be conflated.

For the implementation record, see:

- [`Integration with HACP Sidecar.md`](Integration%20with%20HACP%20Sidecar.md)
- [`HACP Integration Verification Guide.md`](HACP%20Integration%20Verification%20Guide.md)

> **Scope principle:** HACP has broad architectural scope, but intentionally narrow implementation ownership. It coordinates authority mechanisms; it does not seek to replace them.
>
> ---

**Contact:** [digital.humanism.collective@protonmail.com](mailto:digital.humanism.collective@protonmail.com)