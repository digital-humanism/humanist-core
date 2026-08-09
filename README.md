# humanist-core SDK
**Version:** 0.1.0-alpha  
**License:** AGPLv3  
**Based on:** [The Digital Humanism Manifesto](https://github.com/digital-humanism/manifesto)

## Project Goal
Implementation of "Digital Humanism" protocols into LLM frameworks to protect human agency. The SDK prevents autonomous Machine-to-Machine (M2M) loops, protects against cognitive manipulation, and restores the human right to final semantic decision-making.

## Architecture (Status: v0.1.0-alpha)

### 1. `safe_harbor.py` (Cryptographic Safe Harbor)
*Implements Principles 3 and 4 of the Manifesto.*
- **SafeHarborLedger**: Local hash-chain for intent logging. Protects against retroactive tampering.
- **SovereigntyManager**: Consent management and simulation of the "Right to be Forgotten".
- **Status:** ✅ Core logic implemented.

### 2. `loop_breaker.py` (Agency Guard)
*Implements Principle 7.1 (Semantic Checkpoints).*
- **CognitiveLoadAnalyzer**: Biometrics of consciousness. Calculates the minimum time required for a biological human to analyze text.
- **AgencyGuardV2**: Detector for M2M loops and anomalous cognitive velocity.
- **DigitalBlockAnalyzer**: Structural entropy detector (Stub).
- **Status:** ✅ Cognitive load logic implemented. ✅ Embedding-based vector analyzer implemented.

### 3. `integrations/langchain_guard.py` (Immune System)
- **AgencyGuardCallback**: Integration into LangChain via Callbacks. Monitors autonomous agent hops.
- **Status:** ✅ Conceptual integration implemented.

## Quick Start
```bash
pip install -r requirements.txt
