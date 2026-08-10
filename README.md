# humanist-core SDK

![tests](https://github.com/digital-humanism/humanist-core/actions/workflows/tests.yml/badge.svg)

**Version:** v0.4.0-alpha
**License:** AGPLv3  
**Based on:** [The Digital Humanism Manifesto](https://github.com/digital-humanism/manifesto)

## Project Goal
Implementation of "Digital Humanism" protocols into LLM frameworks to protect human agency. The SDK prevents autonomous Machine-to-Machine (M2M) loops, protects against cognitive manipulation, and restores the human right to final semantic decision-making.

## Architecture (Status: v0.2.0-alpha)

## Independent Reviews
- [Digital Humanism as a Commercial Circuit-Breaker and ROI Driver](docs/REVIEW_en.md) — independent AI agent review with a reproducible experiment protocol.

### 1. `safe_harbor.py` (Cryptographic Safe Harbor)
*Implements Principles 3 and 4 of the Manifesto.*
- **SafeHarborLedger**: Local hash-chain for intent logging. Protects against retroactive tampering.
- **SovereigntyManager**: Consent management and simulation of the "Right to be Forgotten".
- **Status:** ✅ Core logic implemented.

### 2. `loop_breaker.py` (Agency Guard)
*Implements Principle 7.1 (Semantic Checkpoints).*
- **CognitiveLoadAnalyzer**: Biometrics of consciousness. Calculates the minimum time required for a biological human to analyze text.
- **AgencyGuardV2**: Detector for M2M loops and anomalous cognitive velocity.
- **DigitalBlockAnalyzer**: Structural entropy detector (embedding-based).
- **Status:** ✅ Cognitive load logic implemented. ✅ Embedding-based vector analyzer implemented.

### 3. `integrations/langchain_guard.py` (Immune System)
- **AgencyGuardCallback**: Integration into LangChain via Callbacks. Monitors autonomous agent hops.
- **Status:** ✅ Conceptual integration implemented.

### 4. `authority.py` (HACP Phase 1 — Authority Core)
*Implements the Authority Core of Architecture v2.0.*
- **IntentEnvelope**: bounded capability space granted by a human.
- **ScopeGuard**: deny-by-default evaluation of proposed actions.
- **DecisionToken**: bounded, expiring human approval — no global flags.
- **Status:** ✅ Phase 1 implemented and tested (invariants 1, 3, 4).

### 5. `boundary.py` (HACP Phase 2 — Boundary Detection)
*Implements risk-weighted autonomy and semantic change detection.*
- **SemanticDeltaGuard**: detects meaningful boundaries (read→write, internal→external, reversible→irreversible)
- **RiskEngine**: context-sensitive risk evaluation across multiple dimensions (irreversibility, externality, privacy, privilege, legal, uncertainty, blast_radius)
- **AutonomyBudget**: cumulative risk budgeting replacing fixed hop counting
- **Status:** ✅ Phase 2 implemented and tested (invariants 2, 5, 7).

### 6. `provenance.py` (HACP Phase 3 — Cryptographic Provenance)
*Causal explainability for consequential actions.*
- **ProvenanceEvent**: immutable graph node with causal parents, payload and policy digests, and a cryptographic signature.
- **EventSigner**: HMAC-SHA256 binding (reference implementation; Ed25519 recommended for production).
- **PolicyDigest**: binds events to the governing policy version — policy change produces a new digest.
- **ProvenanceGraph**: append-only, tamper-detecting graph with `explain()` reconstructing why a consequential action was allowed.
- **Status:** ✅ Phase 3 implemented and tested (Invariant 5).

**Target architecture (v2.0 / HACP):** [docs/ARCHITECTURE_v2.0.md](docs/ARCHITECTURE_v2.0.md) — reference implementation pending (milestone v0.2.0).

## Quick Start
```bash
pip install -r requirements.txt
