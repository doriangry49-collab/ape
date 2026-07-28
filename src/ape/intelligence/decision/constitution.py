from dataclasses import dataclass
from typing import Any, Dict, Tuple


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
    def validate(self, overall_score: int, vector_scores: Dict[str, int]) -> Tuple[str, str, str]:
        """
        Returns (decision, policy, next_step)
        """
        feasibility = vector_scores.get("feasibility", 0)
        demand = vector_scores.get("demand", 0)

        # Constitutional checks
        if feasibility < 20:
            # Too risky, regardless of demand
            return ("IGNORE", "IGNORE", "Do not pursue. Feasibility is catastrophically low.")
        
        if overall_score >= 80:
            return ("BUILD", "BUILD_NOW", "Generate MVP Plan and begin execution.")
        elif overall_score >= 60:
            if demand >= 70:
                msg = "High demand compensates for lower overall score. Build MVP."
                return ("BUILD", "BUILD_NOW", msg)
            else:
                msg = "Create a landing page or survey to validate demand."
                return ("VALIDATE", "VALIDATE_WITH_USERS", msg)
        elif overall_score >= 40:
            return ("WATCH", "WAIT_FOR_SIGNAL", "Set up alerts for competitor or market movement.")
        else:
            return ("IGNORE", "IGNORE", "Score is too low. Discard this opportunity.")

    def evaluate_business_gate(
        self, overall_score: int, evidence_flags: Dict[str, Any]
    ) -> BusinessDecision:
        """
        Enforces Score != Decision logic.
        Requires critical evidence to be True for a BUILD policy.
        """
        willingness = evidence_flags.get("willingness_to_pay_signal")
        target_customer = evidence_flags.get("identifiable_target_customer")
        ai_solvable = evidence_flags.get("ai_solvability")

        # Must have ALL critical evidence to build, regardless of score
        if willingness is not True or target_customer is not True or ai_solvable is not True:
            if overall_score >= 60:
                return BusinessDecision(
                    policy="VALIDATE",
                    message="High score but missing critical evidence. Validate first.",
                )
            elif overall_score >= 40:
                return BusinessDecision(
                    policy="WATCH",
                    message="Moderate score, missing evidence. Monitor.",
                )
            else:
                return BusinessDecision(
                    policy="IGNORE",
                    message="Low score and missing evidence. Discard.",
                )

        # If we have evidence, we still need a decent score
        if overall_score >= 60:
            return BusinessDecision(
                policy="BUILD",
                message="Evidence present and score is high enough. GO.",
            )
        elif overall_score >= 40:
            return BusinessDecision(
                policy="VALIDATE",
                message="Evidence present but score is borderline. Validate.",
            )
        else:
            return BusinessDecision(
                policy="WATCH",
                message="Evidence present but score is low. Watch.",
            )
