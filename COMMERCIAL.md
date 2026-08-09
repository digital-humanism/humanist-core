# Commercial Licensing

humanist-core is free software available under the terms of the
GNU Affero General Public License v3.0 (AGPLv3). See [LICENSE](LICENSE).

Under AGPLv3, if you use humanist-core in a networked service (SaaS),
you must make the corresponding source code of your service available
to users under the same license.

## Need to use humanist-core without AGPLv3 obligations?

The Digital Humanism Initiative offers commercial licensing options
for organizations that require:

- Use in proprietary / closed-source products
- Use in networked services without source disclosure obligations
- Dedicated support, integration assistance, or custom development
- Custom policy configurations for regulated environments

For commercial licensing inquiries, contact: digital.humanism.collective@protonmail.com

## Why paid licenses exist

Commercial licensing funds the continued development of the
humanist-core SDK and the Digital Humanism Initiative.
The AGPLv3 version remains free forever — for individuals,
researchers, and organizations that embrace copyleft.

---

## The Business Case: How "Friction" Multiplies ROI

Counter-intuitively, deliberate cognitive friction accelerates business
outcomes rather than slowing them. The Human Agency Continuity Protocol
(HACP) architecture solves four critical enterprise pain points:

### 1. Dramatic Dev Quality Improvement

Traditional AI-assisted development generates volume over value —
thousands of lines of shallow patches, hallucinated fixes, and
architectural dead ends that create massive technical debt.

**HACP approach:** Semantic Checkpoints force intent fixation and
reduce context noise. The model stops acting as a hyperactive patch
generator and becomes a precision instrument producing 10 lines of
architecturally sound code instead of 1,000 lines of garbage.

**Business impact:**
- 60-80% reduction in debugging time
- Lower technical debt accumulation
- Higher developer satisfaction (professional growth vs. burnout)

### 2. Direct Token OPEX Reduction

Autonomous M2M loops (agent A → agent B → agent C) waste enormous
resources on idle context churn between bots, burning electricity and
API credits without producing useful output.

**HACP approach:** Hop counting and semantic delta detection cut
autonomous loops early. Infrastructure spends resources only on
deliberate, human-authorized inference.

**Business impact:**
- 30-50% reduction in monthly API/token costs
- Lower cloud compute bills
- Reduced environmental footprint

### 3. Capital Protection Against Cascading Failures

When autonomous agent chains loop uncontrollably in production, they
can trigger flash crashes, data corruption, or infrastructure collapse —
turning virtual capital into zero in seconds.

**HACP approach:** Bounded authority and semantic checkpoints prevent
uncontrolled autonomous escalation. High-impact actions require explicit
human authority with bounded Decision Tokens.

**Business impact:**
- Protection against catastrophic production incidents
- Stock price stability (no AI-induced flash crashes)
- Insurance and risk management benefits

### 4. Legal Empowerment (Win-Win for Legal Teams)

Traditional compliance requires expensive NDAs ($5-15K per developer),
ongoing legal oversight, and litigation when leaks inevitably occur.

**HACP approach:**
- **Privacy-preserving logging:** SHA-256 digests of prompts instead
  of raw text — logs contain no readable content, so exposure is
  minimized if they leak
- **Tamper-evidence:** the hash-chain links every record to the
  previous one; any modification is detectable
- **Automated audit trails:** SafeHarbor provides a verifiable chain
  of custody without routine lawyer involvement

**Business impact:**
- NDA costs reduced by ~80% (formality rather than necessity)
- Compliance overhead reduced by 60-80%
- **Legal team freed for strategic work** — routine documentation
  burden is automated, lawyers focus on high-value risk management
  rather than billable hours spent on paperwork
- Companies can redirect saved compliance budget into fixed
  retainers or bonuses for legal staff — creating a win-win

### 5. Professional Growth vs. Cognitive Atrophy

Unlimited AI assistance turns developers into "Tab-key operators" who
experience cognitive atrophy and burnout. After 2-3 years, they cannot
write 10 lines without autocomplete.

**HACP approach:** Cognitive friction and mandatory intent fixation
keep humans as active architects. Semantic Checkpoints create moments
of reflection, preventing the illusion of productivity without real
skill development.

**Business impact:**
- Reduced turnover (people want to work where they grow)
- Higher quality hiring (attracts talent seeking meaningful work)
- Stronger engineering culture

### 6. NDA and Intellectual Property Protection

Leaks to third parties are inevitable. Instead of spending millions
trying to prevent the impossible, HACP makes leaks manageable:
- Digests expose no readable content, so leaked logs carry minimal
  information
- Tamper-evident audit logs demonstrate good-faith operation
- Cryptographic verification establishes authenticity

This shifts the paradigm from "prevent the impossible" to "make leaks
irrelevant."

---

## The Paradox: Friction Accelerates Business

Without HACP: generate 1,000 lines of code in 5 minutes, spend 1 hour
debugging, rewrite everything from scratch.

With HACP: deep analysis in 1 minute, produce 10 architecturally sound
lines that work first time.

The result: faster delivery, lower costs, higher quality, and
protected capital — all by slowing down just enough to think clearly.

---

## Cryptographic Honesty

The v0.1 SafeHarbor implementation provides **tamper-evidence** via a
local hash-chain and **privacy** via SHA-256 digests. To be precise:

- SHA-256(prompt) is a digest, not a zero-knowledge proof.
  Predictable prompts can theoretically be brute-forced by hash
  comparison.
- A local hash-chain detects modification but does not provide
  cryptographic immutability: the journal can still be deleted,
  truncated, or rewritten entirely.
- Strong non-repudiation requires digital signatures, key ownership,
  and external timestamp anchoring.

These limitations are explicitly addressed in the target architecture
**HACP v2.0** ([docs/ARCHITECTURE_v2.0.md](docs/ARCHITECTURE_v2.0.md)),
Section 15 "Cryptographic Provenance", which adds Ed25519 signatures,
external timestamp anchoring, and distributed verification on the
roadmap.

---

## Licensing Summary

| Use case | License | Cost |
|----------|---------|------|
| Individual / research / open-source project | AGPLv3 | Free |
| Internal corporate use (no SaaS) | AGPLv3 | Free |
| SaaS with source code disclosure | AGPLv3 | Free |
| Proprietary SaaS without disclosure | Commercial | Contact us |
| Custom enterprise integration | Commercial | Contact us |
| Dedicated support / consulting | Commercial | Contact us |
