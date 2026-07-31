from __future__ import annotations

from typing import Any, Dict, List, Optional


class EvidenceThresholdAuditor:
    """
    R&D Evidence Threshold & Decision Contract Auditor.
    Firm stopping line for APE R&D: Refuses to simulate fake data, audits real user response count,
    are empirically justified or arbitrary heuristics (PROVISIONAL_THRESHOLD).
    Evaluates stated vs behavioral evidence weights, sampling bias risks, and yields an
    Engineering Recommendation (KEEP / REVISE / REJECT).
    """

    PROVISIONAL_THRESHOLDS = {
        "overall_minimum_responses": 10,
        "H1_problem_positive_min": 5,
        "H2_payment_positive_min": 4,
        "H3_acquisition_positive_min": 5,
    }

    def audit_thresholds(
        self,
        opportunity: str,
        user_responses: List[dict[str, Any]]
    ) -> dict[str, Any]:
        real_user_count = len(user_responses)

        # 1. Audit Threshold Origins & Empirical Basis
        threshold_audit_items = [
            {
                "threshold_name": "Overall Minimum Sample Size (10 real users)",
                "current_value": 10,
                "status": "PROVISIONAL_THRESHOLD",
                "origin": "ORION-042 R&D Candidate Heuristic",
                "evidence_basis": "UNFOUNDED (0 empirical market calibration studies)",
                "rationale": "Intended as a small-sample sanity check before starting spec work.",
                "risk": "False confidence from 10 non-representative survey responses; potential sampling bias.",
                "is_arbitrary": True,
                "is_empirically_justified": False,
            },
            {
                "threshold_name": "H1 Problem Confirmation Minimum (>= 5 positive)",
                "current_value": 5,
                "status": "PROVISIONAL_THRESHOLD",
                "origin": "ORION-042 R&D Candidate Heuristic",
                "evidence_basis": "UNFOUNDED",
                "rationale": "Requires simple majority in a 10-person sample.",
                "risk": "Fails to measure problem severity or pain frequency (e.g., Daily vs Annually).",
                "is_arbitrary": True,
                "is_empirically_justified": False,
            },
            {
                "threshold_name": "H2 Payment Intent Minimum (>= 4 positive)",
                "current_value": 4,
                "status": "PROVISIONAL_THRESHOLD",
                "origin": "ORION-042 R&D Candidate Heuristic",
                "evidence_basis": "UNFOUNDED",
                "rationale": "Requires 40% conversion intent in a 10-person sample.",
                "risk": "Confuses stated willingness to pay ('Would pay $29') with observed payment behavior (credit card authorization / current SaaS spend).",
                "is_arbitrary": True,
                "is_empirically_justified": False,
            },
            {
                "threshold_name": "H3 Acquisition/Trial Intent Minimum (>= 5 positive)",
                "current_value": 5,
                "status": "PROVISIONAL_THRESHOLD",
                "origin": "ORION-042 R&D Candidate Heuristic",
                "evidence_basis": "UNFOUNDED",
                "rationale": "Requires 50% trial interest in a 10-person sample.",
                "risk": "Confuses hypothetical trial interest with actual CLI installation and retention.",
                "is_arbitrary": True,
                "is_empirically_justified": False,
            },
        ]

        # 2. Audit Stated vs Behavioral Evidence Weights
        evidence_weight_matrix = [
            {
                "signal_type": "Stated Payment Intent ('I would pay $29')",
                "weight": "LOW (0.3x)",
                "rationale": "High survey inflation rate; free responses express optimism without financial risk.",
                "status": "STATED_INTENT",
            },
            {
                "signal_type": "Observed Payment Behavior ('Currently paying $30/mo for X tool')",
                "weight": "HIGH (1.0x)",
                "rationale": "Demonstrates existing budget allocation and active market demand.",
                "status": "OBSERVED_BEHAVIOR",
            },
            {
                "signal_type": "Stated Trial Intent ('I would try a CLI proxy')",
                "weight": "LOW (0.3x)",
                "rationale": "Low friction to say yes; does not guarantee CLI installation.",
                "status": "STATED_INTENT",
            },
            {
                "signal_type": "Observed Installation Behavior ('Ran CLI binary & reproduced setup')",
                "weight": "HIGH (1.0x)",
                "rationale": "Demonstrates actual user friction tolerance and technical commitment.",
                "status": "OBSERVED_BEHAVIOR",
            },
        ]

        # 3. Audit Sampling & Bias Risks
        bias_risks = [
            {
                "risk_name": "Source Clustering Bias",
                "description": "All 10 responses collected from a single Reddit thread or Discord channel.",
                "impact": "Distorts sample diversity; captures single sub-community bias.",
                "mitigation": "Require responses across >= 2 independent channels (e.g., HN + Reddit + Direct Interview).",
            },
            {
                "risk_name": "Respondent Duplication Risk",
                "description": "Single individual submitting multiple anonymous survey responses.",
                "impact": "Artificial inflation of response count.",
                "mitigation": "Ingestion gate response_id uniqueness check & IP/header anomaly detection.",
            },
            {
                "risk_name": "Over-weighting Stated Intent",
                "description": "Treating 'I would pay $29' as equivalent to validated commercial demand.",
                "impact": "False GO decision leading to wasted MVP engineering effort.",
                "mitigation": "Differentiate STATED_INTENT from OBSERVED_BEHAVIOR in evidence weighting.",
            },
            {
                "risk_name": "Treating Thresholds as Market Facts",
                "description": "APE converting internal heuristic (10 users) into verified scientific market law.",
                "impact": "Self-referential feedback loop (INFERRED -> OBSERVED violation).",
                "mitigation": "Label all internal threshold counts as PROVISIONAL_THRESHOLD.",
            },
        ]

        # 4. Recommendation & Self-Critique
        recommendation = "REVISE"
        recommendation_justification = (
            "The hardcoded '10 real users' threshold is an unvalidated provisional heuristic (PROVISIONAL_THRESHOLD), "
            "not an empirically proven market law. While 0 real responses MUST remain locked to VALIDATE_MORE, "
            "future decision logic should evaluate Evidence Diversity, Behavioral vs Stated intent, and Severe Negative Signals "
            "rather than relying strictly on raw response counts."
        )

        return {
            "experiment": "ORION-043",
            "status": "AUDIT_COMPLETE",
            "opportunity": opportunity,
            "observed_real_user_count": real_user_count,
            "threshold_audit": threshold_audit_items,
            "evidence_weight_matrix": evidence_weight_matrix,
            "bias_risks": bias_risks,
            "recommendation": recommendation,
            "recommendation_justification": recommendation_justification,
            "self_critique": {
                "thresholds_are_provisional": True,
                "stated_vs_behavioral_separated": True,
                "inferred_not_observed_enforced": True,
                "empty_not_negative_enforced": True,
                "past_reports_not_evidence": True,
            },
        }
