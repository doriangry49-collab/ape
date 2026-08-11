"""
Platform EventBus, MetricsCollector & HealthMonitor — ORION-113 Specification.
Provides centralized EventBus for platform-wide events (ProviderSelected, ProviderFailed, RetryStarted,
CircuitOpened, ExecutionStarted, ExecutionCompleted), MetricsCollector, and dynamic HealthMonitor.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ape.capabilities.adapters_base import ProviderHealth


@dataclass(frozen=True)
class RuntimeEvent:
    """Immutable structural runtime event packet."""
    event_type: str  # ProviderSelected, ProviderFailed, RetryStarted, CircuitOpened, ExecutionStarted, ExecutionCompleted
    capability_id: str
    trace_id: str
    provider_id: str = ""
    model: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """Centralized platform event bus for broadcasting execution telemetry and audit events."""

    def __init__(self) -> None:
        self._subscribers: List[Callable[[RuntimeEvent], None]] = []

    def subscribe(self, subscriber: Callable[[RuntimeEvent], None]) -> None:
        """Subscribe a listener callback function."""
        self._subscribers.append(subscriber)

    def publish(self, event: RuntimeEvent) -> None:
        """Publish a RuntimeEvent to all registered subscribers."""
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception:
                pass


class MetricsCollector:
    """Aggregates execution metrics, token burn rates, latency distributions, and circuit state transitions."""

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._metrics: Dict[str, Dict[str, Any]] = {}
        if event_bus:
            event_bus.subscribe(self.handle_event)

    def handle_event(self, event: RuntimeEvent) -> None:
        p_id = event.provider_id or "global"
        if p_id not in self._metrics:
            self._metrics[p_id] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "latencies_ms": [],
            }

        m = self._metrics[p_id]
        if event.event_type == "ExecutionStarted":
            m["total_calls"] += 1
        elif event.event_type == "ExecutionCompleted":
            m["successful_calls"] += 1
            cost = float(event.details.get("cost", 0.0))
            dur = float(event.details.get("duration_ms", 0.0))
            m["total_cost"] += cost
            m["latencies_ms"].append(dur)
        elif event.event_type in ["ExecutionFailed", "ProviderFailed"]:
            m["failed_calls"] += 1

    def get_metrics(self, provider_id: str = "global") -> Dict[str, Any]:
        return self._metrics.get(provider_id, {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "latencies_ms": [],
        })


class HealthMonitor:
    """Evaluates provider health status derived from MetricsCollector metrics."""

    def __init__(self, metrics_collector: MetricsCollector, failure_threshold: int = 3) -> None:
        self.metrics_collector = metrics_collector
        self.failure_threshold = failure_threshold

    def get_health(self, provider_id: str) -> ProviderHealth:
        m = self.metrics_collector.get_metrics(provider_id)
        failed = m.get("failed_calls", 0)
        total = m.get("total_calls", 0)

        if total > 0 and (failed / total) >= 0.5:
            return ProviderHealth.OFFLINE
        if failed >= self.failure_threshold:
            return ProviderHealth.OFFLINE
        if failed >= 1:
            return ProviderHealth.DEGRADED
        return ProviderHealth.HEALTHY
