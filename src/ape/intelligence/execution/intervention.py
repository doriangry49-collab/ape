"""
Execution Engine — Governed Adaptive Intervention Policy.
ORION-124 (Mission C) Specification.

Consumes risk-calibrated ExecutionHealthSignals across a strict, fail-closed policy
boundary and resolves InterventionProposal outputs (CONTINUE, RETRY, SAFE_HOLD, ABORT).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from ape.intelligence.execution.evaluators import ExecutionHealthSignal, SignalSeverity


class InterventionAction(str, Enum):
    CONTINUE = "CONTINUE"
    RETRY = "RETRY"
    SAFE_HOLD = "SAFE_HOLD"
    ABORT = "ABORT"


@dataclass
class InterventionProposal:
    """
    Deterministic adaptive intervention proposal emitted by GovernedInterventionPolicy.
    Specifies recommended control action, triggering signals, and evidence reference.
    """
    proposed_action: InterventionAction
    severity: SignalSeverity
    trigger_signals: List[ExecutionHealthSignal] = field(default_factory=list)
    reason: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposed_action": self.proposed_action.value,
            "severity": self.severity.value,
            "trigger_signals_count": len(self.trigger_signals),
            "trigger_signals": [s.to_dict() for s in self.trigger_signals],
            "reason": self.reason,
            "evidence_ref": self.evidence_ref,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> InterventionProposal:
        return cls(
            proposed_action=InterventionAction(d.get("proposed_action", "CONTINUE")),
            severity=SignalSeverity(d.get("severity", "LOW")),
            trigger_signals=[
                ExecutionHealthSignal.from_dict(s)
                for s in d.get("trigger_signals", [])
            ],
            reason=str(d.get("reason", "")),
            evidence_ref=str(d.get("evidence_ref", "")),
        )


class GovernedInterventionPolicy:
    """
    Deterministic intervention policy engine.
    Applies fail-closed resolution rules over ExecutionHealthSignal collections.
    """

    def resolve(
        self,
        signals: List[ExecutionHealthSignal],
        current_retry_count: int = 0,
        max_retries: int = 1,
    ) -> InterventionProposal:
        """
        Resolves input health signals to a deterministic InterventionProposal.
        """
        if not signals:
            return InterventionProposal(
                proposed_action=InterventionAction.CONTINUE,
                severity=SignalSeverity.LOW,
                reason="Execution health is nominal. Zero health signals detected.",
            )

        critical_signals = [s for s in signals if s.severity == SignalSeverity.CRITICAL]
        high_signals = [s for s in signals if s.severity == SignalSeverity.HIGH]
        medium_signals = [s for s in signals if s.severity == SignalSeverity.MEDIUM]

        # 1. Any CRITICAL signal (Repeated error loop, evaluator error) -> SAFE_HOLD
        if critical_signals:
            first_crit = critical_signals[0]
            reason_msg = (
                f"Critical execution risk detected ({first_crit.signal_type}): "
                f"{first_crit.message}"
            )
            return InterventionProposal(
                proposed_action=InterventionAction.SAFE_HOLD,
                severity=SignalSeverity.CRITICAL,
                trigger_signals=critical_signals,
                reason=reason_msg,
                evidence_ref=first_crit.evidence_ref,
            )

        # 2. Any HIGH signal (Action ping-pong loop, budget warning)
        if high_signals:
            first_high = high_signals[0]
            if current_retry_count < max_retries:
                reason_msg = (
                    f"High execution risk detected ({first_high.signal_type}). "
                    f"Initiating controlled retry attempt {current_retry_count + 1}/{max_retries}."
                )
                return InterventionProposal(
                    proposed_action=InterventionAction.RETRY,
                    severity=SignalSeverity.HIGH,
                    trigger_signals=high_signals,
                    reason=reason_msg,
                    evidence_ref=first_high.evidence_ref,
                )
            else:
                reason_msg = (
                    f"High execution risk detected ({first_high.signal_type}) "
                    f"and retry budget exhausted ({current_retry_count}/{max_retries})."
                )
                return InterventionProposal(
                    proposed_action=InterventionAction.SAFE_HOLD,
                    severity=SignalSeverity.HIGH,
                    trigger_signals=high_signals,
                    reason=reason_msg,
                    evidence_ref=first_high.evidence_ref,
                )

        # 3. MEDIUM signals (Stagnation without error) -> CONTINUE with advisory
        if medium_signals:
            first_med = medium_signals[0]
            reason_msg = (
                f"Moderate execution signal detected ({first_med.signal_type}). "
                f"Continuing execution under observation."
            )
            return InterventionProposal(
                proposed_action=InterventionAction.CONTINUE,
                severity=SignalSeverity.MEDIUM,
                trigger_signals=medium_signals,
                reason=reason_msg,
                evidence_ref=first_med.evidence_ref,
            )

        return InterventionProposal(
            proposed_action=InterventionAction.CONTINUE,
            severity=SignalSeverity.LOW,
            trigger_signals=signals,
            reason="Execution signals evaluated as LOW risk.",
        )
