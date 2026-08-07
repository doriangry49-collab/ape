"""
Resource & Capacity Management Engine — RFC-022 / Phase B4 Specification.
Handles agent capacity limits, priority queues, and concurrency throttling.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class CapacityManager:
    """Manages Fabric Agent capacity, priority queueing, and workload balancing."""

    def __init__(self, max_concurrent_agents: int = 5) -> None:
        self.max_concurrent_agents = max_concurrent_agents
        self.active_agents_count = 0
        self.queue: List[Dict[str, Any]] = []

    def request_slot(self, agent_name: str, priority: int = 1) -> bool:
        """Request an execution slot for an agent."""
        if self.active_agents_count < self.max_concurrent_agents:
            self.active_agents_count += 1
            return True
        self.queue.append({"agent_name": agent_name, "priority": priority})
        return False

    def release_slot(self) -> Optional[str]:
        """Release slot and return next agent name from queue if any."""
        if self.active_agents_count > 0:
            self.active_agents_count -= 1
        if self.queue:
            next_agent = self.queue.pop(0)
            self.active_agents_count += 1
            return next_agent["agent_name"]
        return None

    def get_capacity_status(self) -> Dict[str, Any]:
        return {
            "max_concurrent": self.max_concurrent_agents,
            "active_agents": self.active_agents_count,
            "queued_agents": len(self.queue),
            "utilization_pct": round((self.active_agents_count / self.max_concurrent_agents) * 100, 2),
        }
