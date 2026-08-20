"""SPEC-0019: Resource Budget Model.

Defines ResourceBudget (6-dimensional limit contract), ResourceUsage (accumulator),
ResourceBudgetExceededError, and the three canonical budget profiles.

Phase 1 enforcement honesty:
  - time_elapsed_seconds: REAL enforcement (monotonic wall-clock via runner).
  - retry_count:          WEAK enforcement (post-stage read from TaskExecutionStage output).
  - tokens_used:          PASSIVE — capabilities layer not wired to pipeline; always 0.
  - cost_usd:             PASSIVE — capabilities layer not wired to pipeline; always 0.0.
  - provider_calls:       PASSIVE — no pipeline-level counter; always {}.
  - search_depth_reached: PASSIVE — no recursive search infrastructure; always 0.

Passive dimensions are structurally present and correctly evaluated by is_exceeded().
They will never trigger enforcement until a future ORION wires the data sources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class ResourceBudgetExceededError(Exception):
    """Raised by ConstitutionalPipelineRunner when a ResourceBudget threshold is reached.

    Enforces SPEC-0019 §3 INV-2: pipeline aborts immediately; caller must not
    continue execution after catching this exception.
    """


@dataclass(frozen=True)
class ResourceBudget:
    """Immutable 6-dimensional execution budget contract (SPEC-0019 §2).

    All Optional fields default to None, meaning that dimension is unconstrained.
    Non-optional fields (max_retries, max_search_depth) always enforce.
    """

    max_tokens: Optional[int] = None
    """Maximum total LLM tokens across all pipeline stages."""

    max_time_seconds: Optional[float] = None
    """Maximum wall-clock duration in seconds for the entire pipeline run."""

    max_cost_usd: Optional[float] = None
    """Maximum estimated API cost in USD across all LLM provider calls."""

    provider_quotas: Dict[str, int] = field(default_factory=dict)
    """Per-provider API call caps, e.g. {"HackerNews": 5, "Gemini": 10}."""

    max_retries: int = 3
    """Maximum total task retry attempts across all TaskExecutionStage runs."""

    max_search_depth: int = 2
    """Maximum recursive research/scanning depth (future use)."""


@dataclass
class ResourceUsage:
    """Mutable accumulator for resource consumption during a pipeline run (SPEC-0019 §2).

    Updated by ConstitutionalPipelineRunner during execution.
    Passive fields are structurally present but remain at their zero values in Phase 1.
    """

    # REAL: updated by runner via time.monotonic()
    time_elapsed_seconds: float = 0.0

    # WEAK: updated post-stage from TaskExecutionStage output_data
    retry_count: int = 0

    # PASSIVE in Phase 1: capabilities layer not wired to pipeline runner
    tokens_used: int = 0
    cost_usd: float = 0.0
    provider_calls: Dict[str, int] = field(default_factory=dict)
    search_depth_reached: int = 0

    def is_exceeded(self, budget: ResourceBudget) -> bool:
        """Returns True if any constrained budget dimension has been reached or exceeded.

        Follows SPEC-0019 §2 is_exceeded() logic exactly.
        Dimensions set to None on the budget are not checked.
        """
        if budget.max_tokens is not None and self.tokens_used >= budget.max_tokens:
            return True
        if budget.max_time_seconds is not None and self.time_elapsed_seconds >= budget.max_time_seconds:
            return True
        if budget.max_cost_usd is not None and self.cost_usd >= budget.max_cost_usd:
            return True
        if self.retry_count > budget.max_retries:
            return True
        if self.search_depth_reached > budget.max_search_depth:
            return True
        for provider, quota in budget.provider_quotas.items():
            if self.provider_calls.get(provider, 0) >= quota:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes usage for evidence log payloads (INV-4 lineage append)."""
        return {
            "time_elapsed_seconds": round(self.time_elapsed_seconds, 3),
            "retry_count": self.retry_count,
            "tokens_used": self.tokens_used,
            "cost_usd": round(self.cost_usd, 6),
            "provider_calls": dict(self.provider_calls),
            "search_depth_reached": self.search_depth_reached,
        }


# ---------------------------------------------------------------------------
# SPEC-0019 §4 — Default Budget Profiles
# ---------------------------------------------------------------------------

DEFAULT_RESEARCH_BUDGET: ResourceBudget = ResourceBudget(
    max_tokens=50_000,
    max_time_seconds=300.0,
    max_cost_usd=1.00,
    max_search_depth=2,
)
"""Research pipeline budget: 50k tokens, 5 min, $1.00, depth 2."""

DEFAULT_EXECUTION_BUDGET: ResourceBudget = ResourceBudget(
    max_tokens=150_000,
    max_time_seconds=600.0,
    max_cost_usd=3.00,
    max_retries=3,
)
"""Execution pipeline budget: 150k tokens, 10 min, $3.00, 3 retries."""

STRICT_CI_BUDGET: ResourceBudget = ResourceBudget(
    max_tokens=20_000,
    max_time_seconds=120.0,
    max_cost_usd=0.25,
    max_retries=1,
)
"""CI budget: 20k tokens, 2 min, $0.25, 1 retry."""
