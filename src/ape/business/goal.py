"""
Goal Root Strategic Domain Entity — ORION-105 Specification.
Defines Goal as the root strategic driver of APE autonomous reasoning loops.
"""

from dataclasses import dataclass, field
import hashlib
import time
from typing import Any, Dict, Optional


@dataclass
class Goal:
    """Root strategic goal statement driving autonomous venture production."""
    goal_id: str
    title: str
    target_market: str = "General Market"
    success_criteria: str = "Produce revenue-generating product venture"
    budget_cap: float = 5000.0
    created_at: float = field(default_factory=time.time)

    @classmethod
    def create(cls, title: str, target_market: str = "General Market", success_criteria: str = "") -> "Goal":
        """Factory constructor for Goal entity."""
        gid = f"goal_{hashlib.sha256(f'{title}:{time.time()}'.encode()).hexdigest()[:10]}"
        return cls(
            goal_id=gid,
            title=title,
            target_market=target_market,
            success_criteria=success_criteria or "Produce revenue-generating product venture",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Goal entity into dictionary payload."""
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "target_market": self.target_market,
            "success_criteria": self.success_criteria,
            "budget_cap": self.budget_cap,
            "created_at": self.created_at,
        }
