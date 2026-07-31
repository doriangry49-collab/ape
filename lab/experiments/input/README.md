# Real User Evidence Input Directory (`lab/experiments/input/`)

**Purpose:** Ingest real-world user survey responses and validation signals into APE without storing Personally Identifiable Information (PII).

---

## Data Schema (`user_responses.json`)

To submit real user feedback, append structured response JSON objects to `lab/experiments/input/user_responses.json`:

```json
[
  {
    "response_id": "resp_001",
    "source": "Reddit r/IndieHackers",
    "timestamp": "2026-07-31T10:00:00Z",
    "target_customer_match": true,
    "current_solution": "Custom Python scripts",
    "problem_frequency": "Daily",
    "current_spend": "$50/mo on developer hours",
    "biggest_pain": "Setup complexity and fragile API breaking changes",
    "trial_interest": true,
    "payment_interest": true,
    "price_feedback": "Willing to pay $20-30/mo",
    "free_text": "Need local caching proxy ASAP.",
    "evidence_type": "USER_REPORTED",
    "is_synthetic": false
  }
]
```

---

## Strict Privacy & PII Invariants

1. **NO PII (Privacy Invariant):** Do NOT include names, email addresses, IP addresses, or phone numbers. Use anonymized `response_id` identifiers (`resp_001`, `resp_002`).
2. **NO Synthetic Data (SPEC-0012 Invariant):** Never generate fake or bot user responses (`is_synthetic: true` triggers an immediate `NO-GO` rejection).
3. **Default State:** When `user_responses.json` is empty (`[]`) or missing, APE evaluates `Observed User Signals = 0` and outputs `VALIDATE_MORE` with `"Waiting for first real user responses (0/10 collected)"`.
