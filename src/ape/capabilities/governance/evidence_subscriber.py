"""
Governance Evidence Subscriber — ORION-119.2 Specification.
Subscribes to platform EventBus events and persists governance trace evidence JSONL records
to .governance/evidence/ without blocking capability execution.
"""

import json
import os
import time
from typing import Optional

from ape.capabilities.resiliency import EventBus, RuntimeEvent


class GovernanceEvidenceSubscriber:
    """Non-blocking EventBus subscriber persisting governance trace evidence to JSONL audit ledgers."""

    def __init__(self, evidence_dir: Optional[str] = None) -> None:
        self.evidence_dir = evidence_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".governance", "evidence")
        )

    def attach_to_event_bus(self, event_bus: EventBus) -> None:
        """Attach subscriber to platform EventBus."""
        event_bus.subscribe(self.handle_event)

    def handle_event(self, event: RuntimeEvent) -> None:
        """Handle incoming RuntimeEvent and append to JSONL ledger via append_to_evidence boundary."""
        try:
            from pathlib import Path
            from ape.utils import append_to_evidence

            track = "decisions" if event.event_type == "GovernedCapabilityStarted" else "execution"

            payload = {
                "event_type": event.event_type,
                "capability_id": event.capability_id,
                "trace_id": event.trace_id,
                "provider_id": event.provider_id,
                "details": event.details,
                "timestamp": event.timestamp,
            }

            append_to_evidence(Path(self.evidence_dir), track, payload)
        except Exception:
            # Non-blocking exception guard: evidence persistence failure NEVER blocks execution
            pass

