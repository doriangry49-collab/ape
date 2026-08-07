# SPEC-0019: Resource Budget Model

**Status:** PROPOSED & FORMALIZED  
**Author:** Lead Architect & Antigravity (Implementation Engineer)  
**Sealed:** 2026-08-06  

---

## 1. Overview & Vision

This specification defines the **Resource Budget Model** for APE. Instead of tightly coupling execution limits to simple token counters, SPEC-0019 introduces a multi-dimensional, abstract `ResourceBudget` interface that governs execution costs, duration, rate limits, search depth, and retry allocations across all engines and stages.

---

## 2. Multi-Dimensional Budget Specification

The budget model encompasses six core dimensions:

```python
from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class ResourceBudget:
    max_tokens: Optional[int] = None           # Maximum total tokens across all LLM calls
    max_time_seconds: Optional[float] = None   # Maximum wall-clock time in seconds
    max_cost_usd: Optional[float] = None       # Maximum estimated API cost in USD
    provider_quotas: Dict[str, int] = field(default_factory=dict) # Per-provider API call caps
    max_retries: int = 3                       # Maximum retry attempts per failed stage/operation
    max_search_depth: int = 2                  # Maximum depth for recursive research/scanning

@dataclass
class ResourceUsage:
    tokens_used: int = 0
    time_elapsed_seconds: float = 0.0
    cost_usd: float = 0.0
    provider_calls: Dict[str, int] = field(default_factory=dict)
    retry_count: int = 0
    search_depth_reached: int = 0

    def is_exceeded(self, budget: ResourceBudget) -> bool:
        if budget.max_tokens and self.tokens_used >= budget.max_tokens:
            return True
        if budget.max_time_seconds and self.time_elapsed_seconds >= budget.max_time_seconds:
            return True
        if budget.max_cost_usd and self.cost_usd >= budget.max_cost_usd:
            return True
        if self.retry_count > budget.max_retries:
            return True
        if self.search_depth_reached > budget.max_search_depth:
            return True
        for provider, quota in budget.provider_quotas.items():
            if self.provider_calls.get(provider, 0) >= quota:
                return True
        return False
```

---

## 3. Governance Invariants & Enforcement

1. **Pre-Stage Budget Validation:** Prior to executing any `PipelineStage`, the `PipelineRunner` MUST check `ResourceUsage.is_exceeded(budget)`.
2. **Fail-Closed Budget Exhaustion:** If a budget threshold is reached or exceeded, the pipeline MUST abort immediately with `ResourceBudgetExceededError` and emit a governance evidence log event (`budget_exhausted`).
3. **No Unbounded Retries:** Stage retries MUST consume the `retry_count` quota; infinite loop or unbounded polling attempts are strictly forbidden.
4. **Usage Lineage Tracking:** `ResourceUsage` data MUST be appended to the stage evidence log (`.governance/evidence/pipeline-YYYY-MM.jsonl`) upon pipeline completion.

---

## 4. Default Budget Profiles

- **`DEFAULT_RESEARCH_BUDGET`**: `max_tokens=50_000`, `max_time_seconds=300`, `max_cost_usd=1.00`, `max_search_depth=2`
- **`DEFAULT_EXECUTION_BUDGET`**: `max_tokens=150_000`, `max_time_seconds=600`, `max_cost_usd=3.00`, `max_retries=3`
- **`STRICT_CI_BUDGET`**: `max_tokens=20_000`, `max_time_seconds=120`, `max_cost_usd=0.25`, `max_retries=1`
