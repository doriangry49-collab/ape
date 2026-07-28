# RFC-012 — Business Discovery Sprint (v2)

**Status:** DESIGN REVISION / PENDING REVIEW  
**Constitutional Basis:** Rule 2 (sealed 2026-07-28)  
> *"APE shall not be used to justify a predetermined product. Business Track product selection must be evidence-driven and emerge from Scan → Research → Decide. Existing ideas are hypotheses, not decisions."*

---

## 1. Mission & Scope

The purpose of this sprint is to systematically discover, score, and validate product opportunities within the Turkish SMB market (focused locally via Kocaeli/Gebze but not limited to it), rather than justifying a pre-selected idea.

### Scope

- **YES:**
  - Pluggable `SignalSource` adapter architecture.
  - Multi-channel business signals: Search/Web demand, Public Complaints, and Job/Manual-work hiring proxy signals.
  - Structured `PainPointExtractor` ensuring strict evidence provenance (no LLM hallucination of facts).
  - Business scoring vectors distinct from final GO/NO-GO gate decisions.
  - Integration with existing `DecisionEngine` via score vs. decision splitting (requiring explicit evidence flags).
  - Final ranked opportunity candidate report.
- **NO:**
  - WhatsApp Business API or Web Chat Simulator code.
  - Database, SaaS, payments, or multi-tenant infrastructure.
  - Emlak Asistanı or any product-specific business logic.
  - LLM-fabricated URLs, references, or signal volumes.

---

## 2. Signal Source Strategy (P0 vs. P1)

To protect the system from breaking changes, network failure, and external rate limits, we isolate dependencies.

### P0 (Core Abstractions & Built-in Providers)
- `SignalSource` abstract boundary.
- File-based/Mock Adapters to guarantee offline testability.
- Public web signals parser (e.g. static RSS/XML feeds or pre-captured business logs).
- Manual job signals parser.

### P1 (Dynamic Remote Integrations — Out of Core Scope)
- `GoogleTrendsAdapter` (external wrapper).
- `RedditAdapter` (praw / JSON endpoint).
- `ŞikayetvarAdapter` / `KariyerNetAdapter` (scraping / API).
*Note: P1 adapters are loaded dynamically and do not block the core scanner execution if they fail or if their libraries are missing.*

---

## 3. Data Models & The `UNKNOWN` State

To prevent bias, all pre-seeded hypotheses (such as the Emlak Asistanı) begin with `UNKNOWN` scores instead of biased priors. We model `UNKNOWN` explicitly in Python, differentiating it from `0` (which implies a verified bad signal).

```python
from dataclasses import dataclass, field
from typing import Literal, Union

# Explicit type representing missing evidence versus zero/bad evidence
UnknownType = Literal["UNKNOWN"]
UNKNOWN: UnknownType = "UNKNOWN"

@dataclass(frozen=True)
class PainPoint:
    source: str
    domain: str                           # e.g., "real_estate", "automotive"
    description: str
    frequency_signal: int | UnknownType = UNKNOWN
    payment_signal: int | UnknownType = UNKNOWN
    market_size: int | UnknownType = UNKNOWN
    demand: int | UnknownType = UNKNOWN
    ai_solvable: bool | UnknownType = UNKNOWN
    evidence_urls: list[str] = field(default_factory=list)
    confidence: float = 0.0
    is_hypothesis: bool = True
```

---

## 4. Evidence Provenance Model

The `PainPointExtractor` must never invent facts. Every extracted business opportunity must contain a traceable line of evidence.

```python
@dataclass(frozen=True)
class EvidenceProvenance:
    source_adapter: str                   # e.g., "job_postings_adapter"
    captured_at: str                      # ISO timestamp
    raw_observation: str                  # Original snippet or text segment
    reference_url: str | None = None       # Source URL
    confidence: float = 1.0               # Trust score of the source channel
```

---

## 5. Score vs. Decision Model

A high score from numeric heuristics (e.g., high search volume) cannot override a critical missing piece of evidence.

### Numeric Score Vectors (0-100)
- `feasibility` (weight: 25%)
- `demand` (weight: 20%)
- `competition` (weight: 15%)
- `payment_signal` (weight: 25%)
- `market_size` (weight: 15%)

### The Decision Gate
The validator assesses the evidence metadata. A `GO` decision requires **all** of the following explicit flags to be present and validated:
1. `willingness_to_pay_signal == True`
2. `identifiable_target_customer == True`
3. `ai_solvability == True`

If any flag is `False` or `UNKNOWN`, the output is restricted to `VALIDATE` (requires user survey/landing page) or `WATCH`, even if the overall numeric score is > 80.

---

## 6. Target Segments (Sprint 1)
- `real_estate`
- `automotive`
- `health_beauty`
- `home_local_services`
- `professional_services`
*(Education segment has been removed).*

---

## 7. Action Plan & TDD Backlog

1. `test_signal_adapters.py`: Verify that dummy/file-based adapters correctly produce normalized `Opportunity` structures.
2. `test_pain_point_extractor.py`: Verify that the extractor correctly extracts `PainPoint` and preserves `EvidenceProvenance` without fabricating fields.
3. `test_scorer_decision_split.py`: Verify that high-scoring topics with missing core evidence are correctly classified as `VALIDATE` or `WATCH` rather than `GO`.
4. Implement interface and classes under `src/ape/intelligence/`.
5. Update `ape scan` CLI to support `--mode=business`.
