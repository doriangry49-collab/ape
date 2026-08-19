"""Domain-specific exceptions for APE Governance Boundary."""

from __future__ import annotations
from typing import Any, Dict, Optional


class GovernanceAuthorizationRequired(Exception):
    """Fired when a high-impact operation is attempted without valid Human Authorization."""

    def __init__(
        self,
        action_semantic: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.action_semantic = action_semantic
        self.reason = reason
        self.details = details or {}
        super().__init__(f"Governance Authorization Denied [{action_semantic}]: {reason}")
