# Architecture

## Overview

The humanist-core SDK implements a three-layer defense system to protect human agency in LLM frameworks. It prevents autonomous Machine-to-Machine (M2M) loops, detects AI masquerading as human, and enforces cryptographic accountability for human decisions.

This is not a collection of separate tools. It is an integrated architecture where each component reinforces the others to create mandatory human presence in AI workflows.

## Core Components

### 1. SafeHarbor (Cryptographic Intent Ledger)

**Purpose:** Immutable logging of human intent with zero-knowledge privacy guarantees.

**Key Design Decisions:**

- **Hash-chain structure** (not traditional database) for tamper-proof history
  - Each record contains SHA-256 hash of previous record
  - Retroactive modification breaks the chain
  - Provides cryptographic proof of sequence

- **SHA-256 of prompts only** (not raw text storage)
  - Protects user privacy (zero-knowledge principle)
  - Allows verification of intent without exposing content
  - Enables legal safe harbor without surveillance

- **Explicit consent tracking** for training data usage
  - Each record includes `consent_training` flag
  - Users can revoke consent via "Right to be Forgotten" transactions

**Why not SQLite or traditional logging:**
Hash-chain provides cryptographic proof of sequence without trusting a centralized database. In adversarial scenarios, append-only hash-chain is more defensible than mutable logs.

**Implementation:** `humanist_core/safe_harbor.py` - `SafeHarborLedger` class

---

### 2. LoopBreaker (Agency Guard)

**Purpose:** Detect M2M loops and AI masquerading as human through three complementary mechanisms.

#### a) Cognitive Load Analyzer

**Novel contribution:** Using cognitive processing time as biometric signature for human presence.

**Formula:**

min_time_seconds = (input_words / 100) * 60 + (output_words / 60) * 60 + 10

**Parameters:**
- **100 WPM** = deep analysis reading speed (not skimming)
  - Based on cognitive science research on critical reading
  - Slower than typical reading (200-250 WPM) because analysis requires reflection
  
- **60 WPM** = deliberate typing speed (not copy-paste)
  - Represents thoughtful composition, not rapid transcription
  - Accounts for cognitive load of formulating critique
  
- **10 seconds** = cognitive friction penalty for context switching
  - Time needed to shift from reading to analysis to response
  - Prevents instantaneous "approval" without comprehension

**Detection logic:**
If a user processes 3,600 words (input) and writes 500 words of critique (output) in 15 seconds:
- Minimum human time = (3600/100)*60 + (500/60)*60 + 10 = 2160 + 500 + 10 = 2,670 seconds (44.5 minutes)
- Actual time = 15 seconds
- **Verdict:** Not human. Block and require verification.

**Why this matters:**
Traditional "human-in-the-loop" systems use manual gates (click to approve). They cannot detect if the "human" is actually an AI agent simulating approval. Cognitive load analysis provides objective biometric verification without requiring eye-tracking, EEG, or other invasive monitoring.

**Implementation:** `humanist_core/loop_breaker.py` - `CognitiveLoadAnalyzer` class

#### b) Digital Block Analyzer

**Novel contribution:** Structural entropy detection of bot farms through digital block similarity.

**Concept:**
- Each user request is treated as a "digital block"
- Humans exhibit high entropy in expression (varied syntax, vocabulary, structure)
- LLMs generate structurally similar outputs even with different prompts
- If 10 consecutive blocks show >50% structural similarity, flag as likely AI generation

**Detection logic:**
- Maintain sliding window of last 10 requests
- Calculate structural hash (or embedding similarity) for each block
- If average similarity across window exceeds threshold, trigger alert

**Why this matters:**
Bot farms often use varied prompts but generate structurally identical responses (same sentence patterns, similar paragraph lengths, repetitive rhetorical structures). Traditional spam detection looks for keywords. Structural entropy detection catches sophisticated generation that varies content but maintains underlying patterns.

**Current status:** **Current status:** ✅ Embedding-based vector analyzer implemented (sentence-transformers, cosine similarity over a sliding window). Structural hashing retained as fallback when sentence-transformers is not installed.

**Implementation:** `humanist_core/loop_breaker.py` - `DigitalBlockAnalyzer` class

#### c) Machine-to-Machine Loop Detection

**Implementation:** Count autonomous hops in agent execution chains.

**Mechanism:**
- Track `hop_count` per session (session_id from parent_run_id in LangChain)
- Each tool execution increments hop counter
- If `hop_count > max_auto_hops` (default: 3) without human checkpoint, raise `AutonomousLoopDetected`
- Force Semantic Checkpoint: require explicit human stance before continuation

**Why this matters:**
Modern agent frameworks (AutoGen, CrewAI, LangGraph) enable chains where Agent A generates a plan, Agent B executes it, Agent C validates results—all without human involvement. This creates "automation theater" where systems appear autonomous but actually amplify human bias at scale. Hop counting provides simple, enforceable limit on autonomous depth.

**Implementation:** `humanist_core/integrations/langchain_guard.py` - `AgencyGuardCallback.on_tool_end()`

---

### 3. LangChain Integration (Immune System)

**Purpose:** Automatic enforcement of humanist principles in agent workflows without requiring code changes.

**Implementation:** Callback-based interception using LangChain's `BaseCallbackHandler`.

**Key callbacks:**

- **`on_chain_start`:** Register human intent
  - Called when user initiates agent workflow
  - Logs intent to SafeHarbor
  - Resets hop counter for new session
  - Establishes baseline for cognitive load tracking

- **`on_tool_end`:** Increment hop counter
  - Called after each tool execution (search, code execution, API calls)
  - Increments `hop_count` for current session
  - Checks against `max_auto_hops` threshold
  - Raises `AutonomousLoopDetected` if exceeded

- **`on_llm_end`:** Check cognitive load if agent requests approval
  - Called after LLM generates response
  - If response contains "PLAN:" or "ACTION REQUIRED:", triggers cognitive load check
  - Verifies that enough time has elapsed for human to read and respond
  - Raises `MasqueradeDetected` if response came too quickly

**Why Callbacks:**
Non-invasive integration. Developers don't need to rewrite agent logic or add explicit checks. The immune system operates at framework level, protecting all agent workflows automatically.

**Implementation:** `humanist_core/integrations/langchain_guard.py` - `AgencyGuardCallback` class

---

## Design Philosophy

### Principle 1: Mandatory Human Agency

The system does not optimize for convenience. It optimizes for human presence.

**Anti-patterns we reject:**
- "Seamless" agent workflows that hide automation from humans
- Auto-approval patterns that simulate human presence without actual human involvement
- Zero-friction interfaces that enable cognitive atrophy and delegation of critical thinking

**Our approach:**
- Semantic Checkpoints force reflection before sensitive operations
- Cognitive friction is a feature, not a bug—it ensures human engagement
- Hash-chain logging makes intent explicit and auditable

**Why this matters:**
In adversarial AI environments, autonomous agents can be weaponized to generate mass manipulation content, simulate grassroots support, and overwhelm critical thinking at scale. If these systems operate without mandatory human checkpoints, they become tools of deception. Our architecture makes autonomous manipulation technically impossible without explicit human authorization.

### Principle 2: Cryptographic Accountability

Every action must be traceable to a specific human decision.

**Implementation:**
- SafeHarbor ledger provides cryptographic proof of intent
- Zero-knowledge hashing protects privacy while enabling verification
- Append-only structure ensures tamper evidence

**Why this matters:**
When AI-generated content causes harm (misinformation, manipulation, incitement), there must be accountability. Current systems allow plausible deniability ("the AI did it"). Our architecture creates clear chain of custody: human intent → system action → cryptographic proof.

### Principle 3: Epistemic Humility

The system acknowledges its limitations and the limits of machine understanding.

**Implementation:**
- Research Context Mode allows users to explicitly declare intent and take responsibility
- Graded responses (explanation, warning, restriction) instead of binary blocks
- Explicit stance requirement before sensitive operations forces users to articulate their position

**Why this matters:**
Corporate AI safety frameworks treat restrictions as "risk management" to avoid liability. This leads to over-censorship and inability to distinguish between legitimate research and malicious use. Our system acknowledges that machines cannot fully understand human intent, and therefore requires humans to explicitly state their position rather than relying on algorithmic judgment.

### Principle 4: Cognitive Friction as Protection

Deliberate slowdowns and verification steps are not obstacles—they are safeguards.

**Implementation:**
- Minimum time requirements based on cognitive processing limits
- Semantic Checkpoints that interrupt automated flows
- Explicit consent and stance requirements before sensitive operations

**Why this matters:**
Speed enables manipulation. When systems operate faster than human comprehension, they can overwhelm critical thinking and create emotional responses before rational analysis. By enforcing cognitive friction, we ensure that human reflection keeps pace with machine execution.

---

## Threat Model

### Protected Against:

1. **Autonomous manipulation farms**
   - Attack: Agents generating persuasive content without human oversight
   - Defense: Hop counting + mandatory human checkpoints
   - Example: Bot network generating thousands of personalized messages

2. **Bot masquerading as human**
   - Attack: AI agents simulating human approval or participation
   - Defense: Cognitive load analysis
   - Example: AI "volunteer" approving plans in 5 seconds

3. **Structural manipulation at scale**
   - Attack: Bot farms with varied prompts but identical underlying structure
   - Defense: Digital block entropy analysis
   - Example: Multiple accounts posting different messages with same rhetorical patterns

4. **Retroactive tampering**
   - Attack: Modifying history of human decisions to create false accountability
   - Defense: Hash-chain ledger
   - Example: Changing intent logs after harmful content is published

5. **Cognitive overload attacks**
   - Attack: Flooding users with requests that exceed human processing capacity
   - Defense: Minimum time requirements
   - Example: Asking users to approve 500-page document in 30 seconds

### Not Protected Against:

1. **Sophisticated social engineering**
   - Humans willingly bypassing checkpoints due to manipulation
   - Defense: User education and interface design (future work)

2. **Advanced adversarial AI**
   - Future models that can simulate human cognitive patterns
   - Defense: Continuous research and model updates (future work)

3. **Physical coercion**
   - Forcing humans to approve agent actions under duress
   - Defense: Out of scope for technical system

4. **Coordinated human manipulation**
   - Multiple humans coordinating to bypass individual checks
   - Defense: Requires sociological solutions, not technical

---

## Comparison to Existing Work

| Approach | Semantic Checkpoints | Cognitive Load Biometrics | M2M Loop Detection | Cryptographic Intent Ledger | Holistic Architecture |
|----------|---------------------|---------------------------|-------------------|----------------------------|---------------------|
| **humanist-core (this SDK)** | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vienna Manifesto on Digital Humanism | ❌ (philosophy only) | ❌ | ❌ | ❌ | ❌ (abstract) |
| Microsoft Open Trust Stack | ✅ (for developers) | ❌ | ❌ | ❌ | ⚠️ (partial) |
| Crab Runtime (arXiv 2511.00592) | ✅ (error recovery) | ❌ | ❌ | ❌ | ⚠️ (partial) |
| Semantic Checkpointing (ResearchGate) | ✅ (state persistence) | ❌ | ❌ | ❌ | ⚠️ (partial) |
| ACRFence (intent-aware fencing) | ✅ (prevent duplicates) | ❌ | ❌ | ❌ | ⚠️ (partial) |
| Human-in-the-Loop patterns | ⚠️ (manual gates) | ❌ | ❌ | ❌ | ⚠️ (partial) |
| Cognitive load measurement (medical/educational) | ❌ | ✅ (eye tracking/EEG) | ❌ | ❌ | ❌ |

**Key distinction:**
Existing work addresses individual components (checkpoints for error recovery, cognitive load for measurement, human-in-the-loop for quality control). No existing work combines these into a holistic system for protecting human agency in adversarial AI environments.

---

## Technical Stack

- **Language:** Python 3.8+
- **Dependencies:** langchain-core (for callback integration)
- **Cryptography:** SHA-256 (stdlib hashlib)
- **Storage:** JSONL files (append-only, hash-chained)
- **Future:** sentence-transformers (for Digital Block Analyzer embeddings)

---

## Future Work

1. **Vector embeddings for Digital Block Analyzer**
   - Replace structural hash with embedding-based similarity
   - Use FAISS or ChromaDB for efficient similarity search
   - Detect semantic similarity beyond structural patterns

2. **Browser extension for web-based Semantic Checkpoints**
   - Intercept AI-generated content in browsers
   - Provide UI for explicit human stance before sharing
   - Integrate with social media platforms

3. **Cryptographic signatures for distributed SafeHarbor**
   - User-controlled keys for intent signing
   - Decentralized verification without centralized ledger
   - Enable cross-platform accountability

4. **Integration with other frameworks**
   - AutoGen callbacks
   - CrewAI middleware
   - LangGraph state checkpoints

5. **Adversarial robustness testing**
   - Red team exercises with sophisticated AI agents
   - Benchmark against state-of-the-art manipulation techniques
   - Continuous improvement of detection algorithms

---

## References

- Digital Humanism Manifesto: https://github.com/digital-humanism/manifesto
- Vienna Manifesto on Digital Humanism: https://ec.europa.eu/futurium/en/european-ai-alliance/vienna-manifesto-digital-humanism.html
- Crab Runtime: https://arxiv.org/html/2604.28138v1
- Semantic Checkpointing: https://www.researchgate.net/publication/399433967
- ACRFence: https://eunomia.dev/blog/2026/05/21/acrfence-preventing-semantic-rollback-attacks-in-agent-checkpoint-restore/
