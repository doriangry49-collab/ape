from __future__ import annotations

from typing import Any, Dict, List, Optional


class ExternalEvidenceCollectionGate:
    """
    R&D External Evidence Collection Gate.
    Firm stopping line for APE R&D: Refuses to simulate fake data, audits real user response count,
    produces the Hypothesis-to-Evidence Matrix, and yields Human Handoff instructions.
    """

    MINIMUM_REAL_RESPONSES_FOR_GO = 10

    def audit_collection_gate(
        self,
        opportunity: str,
        raw_evidence: dict[str, Any],
        user_responses: List[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Audits current real user evidence state and produces the External Collection Gate Report.
        """
        real_user_count = len(user_responses)
        has_synthetic = raw_evidence.get("is_synthetic", False)

        # Hypothesis to Evidence Matrix
        h1_matrix = {
            "hypothesis": "H1 — Problem Exists: Target customers experience severe setup complexity in home_local_services.",
            "current_status": "UNKNOWN" if real_user_count == 0 else "EVALUATED",
            "current_evidence_count": real_user_count,
            "what_counts_as_positive_evidence": "User feedback confirming Daily/Weekly setup pain or manual labor hours.",
            "what_counts_as_negative_evidence": "User feedback stating 'don't have problem', 'no setup pain', or 'current tools are fine'.",
            "what_counts_as_neutral": "Passive comments without pain frequency or tool feedback.",
            "what_remains_unknown": "Exact percentage of target developers experiencing setup friction in production.",
            "minimum_evidence_needed_for_GO": "At least 5 independent real user survey responses confirming setup pain.",
        }

        h2_matrix = {
            "hypothesis": "H2 — Payment Intent: Target customers are willing to pay for a simpler local CLI proxy tool.",
            "current_status": "UNKNOWN" if real_user_count == 0 else "EVALUATED",
            "current_evidence_count": real_user_count,
            "what_counts_as_positive_evidence": "User feedback confirming active commercial spend (SaaS/API > $20/mo) or explicit willingness to pay.",
            "what_counts_as_negative_evidence": "User feedback stating 'won't pay', 'too expensive', 'no budget', or 'prefer free open source'.",
            "what_counts_as_neutral": "Comments regarding pricing models without personal payment intent.",
            "what_remains_unknown": "Price elasticity and acceptable subscription vs one-time license ceiling.",
            "minimum_evidence_needed_for_GO": "At least 4 independent real user survey responses confirming payment intent.",
        }

        h3_matrix = {
            "hypothesis": "H3 — Acquisition / Trial Intent: Developer community outreach yields qualified alpha trial opt-ins.",
            "current_status": "UNKNOWN" if real_user_count == 0 else "EVALUATED",
            "current_evidence_count": real_user_count,
            "what_counts_as_positive_evidence": "Opt-ins to alpha trial or requests for early CLI build access.",
            "what_counts_as_negative_evidence": "Explicit refusal to test alpha builds or disinterest in CLI interface.",
            "what_counts_as_neutral": "General comments on developer communities.",
            "what_remains_unknown": "Actual conversion rate from community forum impressions to alpha CLI trial users.",
            "minimum_evidence_needed_for_GO": "At least 5 independent real user alpha trial opt-ins.",
        }

        # Human Collection Handoff Protocol
        human_handoff = [
            "1. Reach out to target developers in community forums (Reddit r/IndieHackers, Show HN, Discord).",
            "2. Direct users to fill out the 5-question non-leading survey or collect unstructured verbatim feedback.",
            "3. Anonymize user responses to remove PII (do NOT include name, email, phone, address, or IP).",
            "4. Append clean JSON entries to lab/experiments/input/user_responses.json.",
            "5. Verify entries against lab/experiments/input/collection-checklist.md.",
            "6. Re-run python lab/experiments/run_real_user_evidence_analysis.py to process real evidence.",
            "7. Review updated Decision Gate output (VALIDATE_MORE -> GO or NO-GO)."
        ]

        # Stop Condition & Decision Evaluation
        if has_synthetic:
            decision = "NO-GO"
            decision_reason = "Synthetic data detected payload. Immediate rejection."
            status = "INGESTION_REJECTED"
            go_possible = False
        elif real_user_count == 0:
            decision = "VALIDATE_MORE"
            decision_reason = f"Zero real user responses observed (observed_real_user_count = 0). APE MUST STOP and await human evidence collection. GO decision is IMPOSSIBLE without real user evidence."
            status = "WAITING_FOR_REAL_USERS"
            go_possible = False
        else:
            decision = "VALIDATE_MORE"
            decision_reason = f"Logged {real_user_count} real user responses."
            status = "RESPONSES_INGESTED"
            go_possible = real_user_count >= self.MINIMUM_REAL_RESPONSES_FOR_GO

        return {
            "opportunity": opportunity,
            "experiment": "ORION-042",
            "observed_real_user_count": real_user_count,
            "minimum_required_for_GO": self.MINIMUM_REAL_RESPONSES_FOR_GO,
            "evidence_collection_status": status,
            "current_decision": decision,
            "go_possible": go_possible,
            "decision_reason": decision_reason,
            "hypothesis_matrix": {
                "H1_problem_exists": h1_matrix,
                "H2_payment_intent": h2_matrix,
                "H3_acquisition_trial_intent": h3_matrix,
            },
            "unsupported_previous_hypotheses": [
                "$29 one-time CLI developer license (UNSUPPORTED - 0 payment intent evidence)",
                "Direct developer community outreach (UNSUPPORTED - 0 conversion evidence)",
                "50 active developers in 14 days target (UNVERIFIED PROPOSED THRESHOLD)",
            ],
            "human_collection_handoff": human_handoff,
            "evidence_integrity_rules": [
                "INFERRED != OBSERVED: Past APE report conclusions are NOT customer evidence.",
                "SYNTHETIC != REAL: AI-generated responses trigger immediate NO-GO rejection.",
                "NO PII: Forbidden fields (name, email, phone) trigger payload rejection.",
                "NO FAKE DEFAULTS: Omitted fields remain UNKNOWN.",
                "EMPTY != NEGATIVE: 0 responses means WAITING_FOR_REAL_USERS, NOT customer rejection."
            ],
            "stop_rule": "APE MUST STOP simulation and wait for external real user evidence to be appended to lab/experiments/input/user_responses.json."
        }
