from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ape.intelligence.decision.bridge import BridgeResult
from ape.intelligence.decision.models import PolicyDecision, PolicyGateResult


@dataclass
class BusinessDecision:
    policy: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# CONSTITUTIONAL RULES (append-only — each rule is permanently sealed)
# ─────────────────────────────────────────────────────────────────────────────
#
# Rule 1 (RFC-010, sealed 2026-07-28):
#   Docker host environment must NEVER be passed to sandboxed containers.
#   Security boundary: env={} is mandatory in all DockerSandboxExecutor calls.
#
# Rule 2 (RFC-011/Business-Track, sealed 2026-07-28):
#   APE shall not be used to justify a predetermined product.
#   Business Track product selection must be evidence-driven and emerge from
#   the Scan → Research → Decide pipeline.
#   Existing ideas are HYPOTHESES, not decisions.
#   A product candidate MUST pass through Decision Engine with GO/NO-GO before
#   any implementation is started.
# ─────────────────────────────────────────────────────────────────────────────


BUSINESS_TRACK_RULE = (
    "APE shall not be used to justify a predetermined product. "
    "Business Track product selection must be evidence-driven and emerge from "
    "Scan → Research → Decide. Existing ideas are hypotheses, not decisions."
)


class ConstitutionValidator:
    """
    Ensures that the raw scores comply with the APE constitution
    and maps them to a concrete decision and policy.
    """

    def evaluate_policy(
        self,
        overall_score: int,
        vector_scores: Dict[str, int],
        bridge_result: Optional[BridgeResult] = None,
        evidence_flags: Optional[Dict[str, Any]] = None,
    ) -> PolicyGateResult:
        """
        RFC-013 Unified Policy Gate Evaluation:
        Consolidates score breakdown + observation inference flags into a canonical PolicyGateResult.
        """
        if bridge_result is not None:
            flags = bridge_result.evidence_flags
        elif evidence_flags is not None:
            flags = evidence_flags
        else:
            flags = {}

        feasibility = vector_scores.get("feasibility", 100)

        # Rule 1: Constitutional Hard Stop (Feasibility)
        if feasibility < 20:
            return PolicyGateResult(
                decision=PolicyDecision.IGNORE,
                policy_code="IGNORE",
                message="Do not pursue. Feasibility is catastrophically low.",
                rule_id="RULE_FEASIBILITY_HARD_STOP",
            )

        if not flags:
            # Fall back to standard score validation (Legacy / Tech track mode)
            demand = vector_scores.get("demand", 0)
            if overall_score >= 80:
                return PolicyGateResult(
                    decision=PolicyDecision.BUILD,
                    policy_code="BUILD_NOW",
                    message="Generate MVP Plan and begin execution.",
                    rule_id="RULE_GO_BUILD_APPROVED",
                )
            elif overall_score >= 60:
                if demand >= 70:
                    return PolicyGateResult(
                        decision=PolicyDecision.BUILD,
                        policy_code="BUILD_NOW",
                        message="High demand compensates for lower overall score. Build MVP.",
                        rule_id="RULE_GO_BUILD_APPROVED",
                    )
                else:
                    return PolicyGateResult(
                        decision=PolicyDecision.VALIDATE,
                        policy_code="VALIDATE_WITH_USERS",
                        message="Create a landing page or survey to validate demand.",
                        rule_id="RULE_GO_VALIDATE_BORDERLINE",
                    )
            elif overall_score >= 40:
                return PolicyGateResult(
                    decision=PolicyDecision.WATCH,
                    policy_code="WAIT_FOR_SIGNAL",
                    message="Set up alerts for competitor or market movement.",
                    rule_id="RULE_GO_WATCH_LOW_SCORE",
                )
            else:
                return PolicyGateResult(
                    decision=PolicyDecision.IGNORE,
                    policy_code="IGNORE",
                    message="Score is too low. Discard this opportunity.",
                    rule_id="RULE_EVIDENCE_GATE_LOW_SCORE",
                )

        payment_signal = flags.get("payment_signal")
        target_customer = flags.get("identifiable_customer")
        ai_solvable = flags.get("ai_solvability")

        has_all_evidence = (
            payment_signal is True and target_customer is True and ai_solvable is True
        )

        if not has_all_evidence:
            if overall_score >= 60:
                return PolicyGateResult(
                    decision=PolicyDecision.VALIDATE,
                    policy_code="VALIDATE_WITH_USERS",
                    message="High score but missing critical evidence. Validate first.",
                    rule_id="RULE_EVIDENCE_GATE_MISSING_EVIDENCE",
                )
            elif overall_score >= 40:
                return PolicyGateResult(
                    decision=PolicyDecision.WATCH,
                    policy_code="WAIT_FOR_SIGNAL",
                    message="Moderate score, missing evidence. Monitor.",
                    rule_id="RULE_EVIDENCE_GATE_BORDERLINE_SCORE",
                )
            else:
                return PolicyGateResult(
                    decision=PolicyDecision.IGNORE,
                    policy_code="IGNORE",
                    message="Low score and missing evidence. Discard.",
                    rule_id="RULE_EVIDENCE_GATE_LOW_SCORE",
                )

        # Complete evidence verified
        if overall_score >= 60:
            return PolicyGateResult(
                decision=PolicyDecision.BUILD,
                policy_code="BUILD_NOW",
                message="Evidence verified and score meets threshold. GO.",
                rule_id="RULE_GO_BUILD_APPROVED",
            )
        elif overall_score >= 40:
            return PolicyGateResult(
                decision=PolicyDecision.VALIDATE,
                policy_code="VALIDATE_WITH_USERS",
                message="Evidence present but score is borderline. Validate.",
                rule_id="RULE_GO_VALIDATE_BORDERLINE",
            )
        else:
            return PolicyGateResult(
                decision=PolicyDecision.WATCH,
                policy_code="WAIT_FOR_SIGNAL",
                message="Evidence present but score is low. Watch.",
                rule_id="RULE_GO_WATCH_LOW_SCORE",
            )

    def validate(self, overall_score: int, vector_scores: Dict[str, int]) -> Tuple[str, str, str]:
        """
        Legacy interface — returns (decision, policy_code, next_step) tuple.
        Preserved for backward compatibility.

        IMPORTANT: Contains zero independent policy branching.
        Delegates entirely to evaluate_policy() which is the sole canonical
        policy evaluator per RFC-013 / SPEC-0013.
        """
        result = self.evaluate_policy(
            overall_score=overall_score,
            vector_scores=vector_scores,
            bridge_result=None,
        )
        return (result.decision.value, result.policy_code, result.message)

    def evaluate_business_gate(
        self,
        overall_score: int,
        evidence_flags: Dict[str, Any],
        vector_scores: Optional[Dict[str, int]] = None,
    ) -> BusinessDecision:
        """
        Enforces Score != Decision logic.
        Delegates to evaluate_policy for consistency.

        Args:
            overall_score: Weighted composite score (0-100).
            evidence_flags: Inferred signal flags from InferenceBridge.
            vector_scores: Optional breakdown including 'feasibility'.
                           Pass the real feasibility score here to ensure
                           the constitutional hard-stop (feasibility < 20)
                           is evaluated. Defaults to {} which treats
                           feasibility as 100 — callers SHOULD supply this.
        """
        res = self.evaluate_policy(
            overall_score=overall_score,
            vector_scores=vector_scores or {},
            evidence_flags=evidence_flags,
        )
        return BusinessDecision(
            policy=res.decision.value,
            message=res.message,
        )

