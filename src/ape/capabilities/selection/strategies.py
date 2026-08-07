"""
Modular Provider Selection Strategies Package — ORION-114 Specification.
Provides LowestCostStrategy, LowestLatencyStrategy, HighestQualityStrategy,
LocalOnlyStrategy, BalancedStrategy, BudgetStrategy, PinnedStrategy, and FallbackStrategy.
"""

from typing import List, Protocol, runtime_checkable

from ape.capabilities.adapters_base import ProviderAdapter
from ape.capabilities.contracts import ExecutionContext, ProviderUnavailableError
from ape.capabilities.registry import ProviderScore


@runtime_checkable
class ProviderSelectionStrategy(Protocol):
    """Plugin strategy interface for provider selection."""
    strategy_name: str

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        ...


class PinnedStrategy:
    """Selects a specific pinned provider_id."""
    strategy_name: str = "PINNED"

    def __init__(self, pinned_provider_id: str) -> None:
        self.pinned_provider_id = pinned_provider_id

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        for adapter in candidates:
            if adapter.provider_id == self.pinned_provider_id:
                return adapter
        raise ProviderUnavailableError(f"Pinned provider '{self.pinned_provider_id}' is not in candidate list.")


class LowestCostStrategy:
    """Selects the candidate provider adapter with the lowest cost per 1k tokens."""
    strategy_name: str = "LOWEST_COST"

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        if not candidates:
            raise ProviderUnavailableError("No candidates available for LowestCostStrategy.")
        sorted_candidates = sorted(candidates, key=lambda a: a.profile.cost_per_1k_tokens)
        return sorted_candidates[0]


class LowestLatencyStrategy:
    """Selects the candidate provider adapter with the lowest average latency."""
    strategy_name: str = "LOWEST_LATENCY"

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        if not candidates:
            raise ProviderUnavailableError("No candidates available for LowestLatencyStrategy.")
        sorted_candidates = sorted(candidates, key=lambda a: a.profile.cost_per_1k_tokens)
        return sorted_candidates[0]


class HighestQualityStrategy:
    """Selects the candidate provider adapter with the highest quality rating."""
    strategy_name: str = "HIGHEST_QUALITY"

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        if not candidates:
            raise ProviderUnavailableError("No candidates available for HighestQualityStrategy.")
        sorted_candidates = sorted(
            candidates,
            key=lambda a: (
                2.0 if a.features().reasoning and a.profile.cost_per_1k_tokens > 0.002 else (1.0 if a.features().reasoning else 0.0)
            ),
            reverse=True,
        )
        return sorted_candidates[0]


class LocalOnlyStrategy:
    """Selects only local LLMs ($0.00 token cost)."""
    strategy_name: str = "LOCAL_ONLY"

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        local_candidates = [a for a in candidates if a.profile.cost_per_1k_tokens == 0.000 or "local" in a.profile.display_name.lower()]
        if not local_candidates:
            raise ProviderUnavailableError("No local LLM candidates available for LocalOnlyStrategy.")
        return local_candidates[0]


class BalancedStrategy:
    """Selects provider using balanced multi-dimensional ProviderScore (quality, latency, cost)."""
    strategy_name: str = "BALANCED"

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        if not candidates:
            raise ProviderUnavailableError("No candidates available for BalancedStrategy.")
        sorted_candidates = sorted(
            candidates,
            key=lambda a: ProviderScore(
                provider_id=a.provider_id,
                cost=a.profile.cost_per_1k_tokens,
                confidence=95.0 if a.features().supports('reasoning') else 80.0,
            ).score,
            reverse=True,
        )
        return sorted_candidates[0]


class BudgetStrategy:
    """Selects candidate prioritizing maximum context tokens within budget constraints."""
    strategy_name: str = "BUDGET"

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        if not candidates:
            raise ProviderUnavailableError("No candidates available for BudgetStrategy.")
        sorted_candidates = sorted(candidates, key=lambda a: a.profile.cost_per_1k_tokens)
        return sorted_candidates[0]


class FallbackStrategy:
    """Selects the first available healthy provider adapter in candidate list."""
    strategy_name: str = "FALLBACK"

    def select_provider(self, candidates: List[ProviderAdapter], context: ExecutionContext) -> ProviderAdapter:
        if not candidates:
            raise ProviderUnavailableError("No candidates available for FallbackStrategy.")
        return candidates[0]


# Alias for backwards compatibility
BestScoreStrategy = HighestQualityStrategy
