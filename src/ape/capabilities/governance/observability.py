"""
Capability Observability & Performance Signals Contract — ORION-119.F Specification.
Tracks unblended performance metrics and enforces Measurement ≠ Governance Policy invariant.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class PerformanceSignal:
    """Unblended performance metric record for capability resolution decision support."""
    target_id: str
    success_rate: float = 100.0
    latency_ms: float = 0.0
    cost: float = 0.0
    reliability_score: float = 100.0
    total_calls: int = 0
    failed_calls: int = 0
    updated_at: float = field(default_factory=time.time)


class CapabilityObservabilityStore:
    """Stores unblended performance signals. Enforces Measurement ≠ Governance Policy invariant."""

    def __init__(self) -> None:
        self._signals: Dict[str, PerformanceSignal] = {}

    def record_observation(self, target_id: str, success: bool, latency_ms: float, cost: float = 0.0) -> PerformanceSignal:
        """Record performance observation without mutating governance policies."""
        current = self._signals.get(target_id, PerformanceSignal(target_id=target_id))

        total = current.total_calls + 1
        failed = current.failed_calls + (0 if success else 1)
        sr = round(((total - failed) / total) * 100.0, 2)
        avg_lat = round(((current.latency_ms * current.total_calls) + latency_ms) / total, 2)
        tot_cost = round(current.cost + cost, 4)
        rel = max(0.0, sr - (failed * 2.0))

        updated = PerformanceSignal(
            target_id=target_id,
            success_rate=sr,
            latency_ms=avg_lat,
            cost=tot_cost,
            reliability_score=rel,
            total_calls=total,
            failed_calls=failed,
        )

        self._signals[target_id] = updated
        return updated

    def get_signal(self, target_id: str) -> Optional[PerformanceSignal]:
        """Return performance signal record."""
        return self._signals.get(target_id)
