"""
Resource & Execution Budget Specification — ORION-111B.
Provides immutable ExecutionBudget limits and mutable ExecutionUsage tracker with limit enforcement.
"""

from dataclasses import dataclass
from typing import Any, Dict

from ape.capabilities.contracts import BudgetExceededError, CapabilityResult


@dataclass(frozen=True)
class ExecutionBudget:
    """Immutable execution budget bounds dataclass."""
    max_tokens: int = 100000
    max_cost: float = 1.00
    max_latency_seconds: float = 60.0
    max_api_calls: int = 50


@dataclass
class ExecutionUsage:
    """Mutable accrued resource usage accumulator."""
    tokens_used: int = 0
    cost_accrued: float = 0.0
    latency_ms_total: float = 0.0
    api_calls_count: int = 0

    def record_execution(self, result: CapabilityResult) -> None:
        """Record capability execution metrics into usage accumulator."""
        self.api_calls_count += 1
        self.cost_accrued += result.cost
        self.latency_ms_total += result.duration_ms
        if result.token_usage:
            self.tokens_used += result.token_usage.get("total_tokens", 0)

    def validate_budget(self, budget: ExecutionBudget) -> None:
        """Verify accrued usage against immutable budget limits. Raises BudgetExceededError on breach."""
        if self.tokens_used > budget.max_tokens:
            raise BudgetExceededError(f"Execution tokens used ({self.tokens_used}) exceeded budget limit ({budget.max_tokens}).")
        if self.cost_accrued > budget.max_cost:
            raise BudgetExceededError(f"Execution cost accrued (${self.cost_accrued:.4f}) exceeded budget limit (${budget.max_cost:.4f}).")
        if self.api_calls_count > budget.max_api_calls:
            raise BudgetExceededError(f"Execution API calls ({self.api_calls_count}) exceeded budget limit ({budget.max_api_calls}).")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokens_used": self.tokens_used,
            "cost_accrued": round(self.cost_accrued, 4),
            "latency_ms_total": round(self.latency_ms_total, 2),
            "api_calls_count": self.api_calls_count,
        }
