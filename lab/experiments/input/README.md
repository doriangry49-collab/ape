# Evidence Collection & Ingestion Guide (`lab/experiments/input/`)

**Purpose:** This directory serves as the human-in-the-loop evidence ingestion point for real-world user feedback on APE market opportunities.

---

## Strict Rules of Evidence Authenticity

### 1. What Counts as Real User Evidence?
- Direct feedback from an external human user collected via Reddit, HackerNews, surveys, landing page signups, or 1-on-1 interviews.
- Verified behavioral quotes regarding current manual workarounds, setup pain frequency, or commercial spending.

### 2. What Does NOT Count as Evidence?
- **APE Report Content:** Information copied from previous APE reports (e.g. `$29 license hypothesis`, `50 devs in 14 days target`) is **analytical inference**, NOT customer evidence.
- **Synthetic / Bot Data:** Any AI-generated or simulated survey responses (`is_synthetic: true` results in immediate `NO-GO` rejection).
- **Internal Hypotheses:** Team assumptions or unverified roadmap goals.

### 3. Key Invariants
- **`INFERRED != OBSERVED`:** Hypotheses created by LLMs or heuristic scorers can NEVER raise confidence or count as observed evidence.
- **`SYNTHETIC != REAL`:** Synthetic data payloads are rejected at the ingestion gate.
- **Zero Real Users = Zero Evidence:** If `user_responses.json` contains 0 entries, APE outputs `Observed Responses: 0`, `Decision: VALIDATE_MORE`, and `GO: IMPOSSIBLE`.

---

## Schema & Privacy Invariants

### Forbidden PII Fields
To comply with privacy standards, **do NOT include PII**:
- `name`
- `email`
- `phone`
- `address`
- `ip`

Use anonymous IDs (`resp_001`, `resp_002`).

### Ingestion Data Contract (`user_responses.json`)

```json
[
  {
    "response_id": "resp_001",
    "source": "reddit",
    "target_customer_match": true,
    "problem_frequency": "Daily",
    "trial_interest": true,
    "payment_interest": true,
    "current_spend": "$50/mo",
    "free_text": "Manual API integration breaks weekly."
  }
]
```

### Valid Sources
- `reddit`
- `hackernews`
- `direct_interview`
- `survey`
- `landing_page`
- `other`
- `UNKNOWN` (if source not specified)
