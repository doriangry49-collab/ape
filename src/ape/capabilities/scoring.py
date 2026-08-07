"""
ProviderEvaluation & ProviderScoreCalculator Strategies — ORION-115 Specification.
Provides ProviderEvaluation detailed scoring breakdown and decoupled ProviderScoreCalculator strategies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Protocol, runtime_checkable

from ape.capabilities.adapters_base import ProviderAdapter
from ape.capabilities.contracts import ExecutionContext


@dataclass(frozen=True)
class ProviderEvaluation:
    """Detailed multi-dimensional provider score breakdown with component ratings, weights, and explanation reasons."""
    provider_id: str
    score: float
    reasons: List[str] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=dict)
    component_scores: Dict[str, float] = field(default_factory=dict)


@runtime_checkable
class ProviderScoreCalculator(Protocol):
    """Calculator interface producing ProviderEvaluation ratings for candidate adapters."""
    calculator_name: str

    def calculate_evaluation(self, adapter: ProviderAdapter, context: ExecutionContext) -> ProviderEvaluation:
        ...


class CostFirstCalculator:
    """Prioritizes lowest cost per token."""
    calculator_name: str = "COST_FIRST"

    def calculate_evaluation(self, adapter: ProviderAdapter, context: ExecutionContext) -> ProviderEvaluation:
        cost = adapter.profile.cost_per_1k_tokens
        score = max(0.0, round((1.0 - (cost / 0.01)) * 100.0, 2))
        return ProviderEvaluation(
            provider_id=adapter.provider_id,
            score=score,
            reasons=[f"Token cost is ${cost:.4f} per 1k tokens"],
            weights={"cost": 1.0},
            component_scores={"cost": score},
        )


class LatencyFirstCalculator:
    """Prioritizes low average response latency."""
    calculator_name: str = "LATENCY_FIRST"

    def calculate_evaluation(self, adapter: ProviderAdapter, context: ExecutionContext) -> ProviderEvaluation:
        score = 95.0 if "ollama" in adapter.provider_id else 80.0
        return ProviderEvaluation(
            provider_id=adapter.provider_id,
            score=score,
            reasons=["Latency estimation evaluated"],
            weights={"latency": 1.0},
            component_scores={"latency": score},
        )


class EnterpriseCalculator:
    """Prioritizes high reasoning quality, compliance, and zero failure rates."""
    calculator_name: str = "ENTERPRISE"

    def calculate_evaluation(self, adapter: ProviderAdapter, context: ExecutionContext) -> ProviderEvaluation:
        reasoning_score = 100.0 if adapter.features().reasoning else 70.0
        return ProviderEvaluation(
            provider_id=adapter.provider_id,
            score=reasoning_score,
            reasons=["Enterprise reasoning quality evaluated"],
            weights={"quality": 0.8, "availability": 0.2},
            component_scores={"quality": reasoning_score, "availability": 99.9},
        )


class BalancedCalculator:
    """Balanced evaluation across quality, latency, availability, and cost."""
    calculator_name: str = "BALANCED"

    def calculate_evaluation(self, adapter: ProviderAdapter, context: ExecutionContext) -> ProviderEvaluation:
        quality = 95.0 if adapter.features().reasoning else 80.0
        cost_score = max(0.0, (1.0 - (adapter.profile.cost_per_1k_tokens / 0.01)) * 100.0)
        final_score = round((quality * 0.6) + (cost_score * 0.4), 2)
        return ProviderEvaluation(
            provider_id=adapter.provider_id,
            score=final_score,
            reasons=[f"Balanced rating: Quality {quality}, CostScore {cost_score:.1f}"],
            weights={"quality": 0.6, "cost": 0.4},
            component_scores={"quality": quality, "cost": cost_score},
        )
