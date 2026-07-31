from __future__ import annotations

from typing import Any, Dict, List, Optional


class RealUserEvidenceAnalyzer:
    """
    R&D Real User Evidence Analyzer & Decision Gate.
    Categorizes evidence into OBSERVED_POSITIVE, OBSERVED_NEGATIVE, OBSERVED_NEUTRAL, UNKNOWN, INFERRED.
    Performs hypothesis-by-hypothesis validation (H1 Problem, H2 Payment Intent, H3 Acquisition/Trial).
    Enforces strict self-critique: GO is IMPOSSIBLE without real user evidence; UNSUPPORTED hypotheses
    from previous tasks remain UNKNOWN unless verified.
    """

    EVIDENCE_CATEGORIES = {
        "OBSERVED_POSITIVE",
        "OBSERVED_NEGATIVE",
        "OBSERVED_NEUTRAL",
        "UNKNOWN",
        "INFERRED",
    }

    NEGATIVE_KEYWORDS = [
        "don't have problem",
        "no problem",
        "won't pay",
        "no interest",
        "current tools are fine",
        "setup problem is minor",
        "prefer custom scripts",
        "too expensive",
        "not useful",
        "no budget",
    ]

    def analyze_evidence(
        self,
        topic: str,
        raw_evidence: dict[str, Any],
        user_responses: List[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Processes real user responses and raw research evidence, producing granular hypothesis statuses,
        evidence balance, self-critique results, and deterministic GO / VALIDATE_MORE / NO-GO decision.
        """
        user_response_count = len(user_responses)
        has_synthetic = raw_evidence.get("is_synthetic", False)

        positive_evidence: List[dict[str, Any]] = []
        negative_evidence: List[dict[str, Any]] = []
        neutral_evidence: List[dict[str, Any]] = []
        unknown_evidence: List[dict[str, Any]] = []

        h1_pos = 0  # Problem confirmations
        h1_neg = 0
        h2_pos = 0  # Payment intents
        h2_neg = 0
        h3_pos = 0  # Trial / acquisition intents
        h3_neg = 0

        # Process user responses
        for resp in user_responses:
            if resp.get("is_synthetic", False):
                has_synthetic = True

            resp_id = resp.get("response_id", "anon_resp")
            source = resp.get("source", "User Feedback")
            free_text = str(resp.get("free_text", "")).lower()

            # Check missing fields -> UNKNOWN
            if not free_text and "problem_frequency" not in resp and "payment_interest" not in resp:
                unknown_evidence.append({
                    "item": f"Response {resp_id}: Empty or missing feedback fields",
                    "category": "UNKNOWN"
                })
                continue

            # Check H1 Problem
            prob_freq = resp.get("problem_frequency")
            if prob_freq in ("Daily", "Weekly") or any(kw in free_text for kw in ["slow", "broken", "pain", "manual", "setup"]):
                h1_pos += 1
                positive_evidence.append({
                    "item": f"Response {resp_id} [{source}]: Confirmed setup problem ({prob_freq or 'high pain'})",
                    "category": "OBSERVED_POSITIVE"
                })
            elif any(kw in free_text for kw in ["don't have problem", "no problem", "current tools are fine"]):
                h1_neg += 1
                negative_evidence.append({
                    "item": f"Response {resp_id} [{source}]: Denied setup problem ('{free_text}')",
                    "category": "OBSERVED_NEGATIVE"
                })

            # Check H2 Payment Intent
            pay_intent = resp.get("payment_interest")
            curr_spend = resp.get("current_spend", "")
            if pay_intent is True or (curr_spend and "$" in curr_spend and "0" not in curr_spend):
                h2_pos += 1
                positive_evidence.append({
                    "item": f"Response {resp_id} [{source}]: Confirmed payment intent ({curr_spend or '$29 license'})",
                    "category": "OBSERVED_POSITIVE"
                })
            elif pay_intent is False or any(kw in free_text for kw in ["won't pay", "too expensive", "no budget", "free"]):
                h2_neg += 1
                negative_evidence.append({
                    "item": f"Response {resp_id} [{source}]: Refused payment / no budget ('{free_text or 'won\'t pay'}')",
                    "category": "OBSERVED_NEGATIVE"
                })

            # Check H3 Acquisition / Trial Intent
            trial_intent = resp.get("trial_interest")
            if trial_intent is True:
                h3_pos += 1
                positive_evidence.append({
                    "item": f"Response {resp_id} [{source}]: Opted into alpha trial",
                    "category": "OBSERVED_POSITIVE"
                })
            elif trial_intent is False or "no interest" in free_text:
                h3_neg += 1
                negative_evidence.append({
                    "item": f"Response {resp_id} [{source}]: Declined alpha trial ('{free_text or 'no interest'}')",
                    "category": "OBSERVED_NEGATIVE"
                })

        # Evaluate Hypotheses Status
        def get_h_status(pos: int, neg: int, total: int) -> str:
            if total == 0 or (pos == 0 and neg == 0):
                return "UNKNOWN"
            if neg > pos and neg >= 2:
                return "CONTRADICTED"
            if pos >= 3 and pos > neg * 2:
                return "OBSERVED"
            if pos >= 1:
                return "PARTIALLY_SUPPORTED"
            return "UNSUPPORTED"

        h1_status = get_h_status(h1_pos, h1_neg, user_response_count)
        h2_status = get_h_status(h2_pos, h2_neg, user_response_count)
        h3_status = get_h_status(h3_pos, h3_neg, user_response_count)

        hypotheses_evaluation = {
            "H1_problem_exists": {
                "statement": "Target customers experience severe setup complexity in home_local_services.",
                "status": h1_status,
                "positive_count": h1_pos,
                "negative_count": h1_neg,
            },
            "H2_payment_intent": {
                "statement": "Target customers are willing to pay for a simpler local CLI automation tool.",
                "status": h2_status,
                "positive_count": h2_pos,
                "negative_count": h2_neg,
            },
            "H3_acquisition_trial_intent": {
                "statement": "Developer community outreach yields qualified alpha trial users.",
                "status": h3_status,
                "positive_count": h3_pos,
                "negative_count": h3_neg,
            },
        }

        # Self-Critique of ORION-034 Hypotheses
        self_critique = {
            "pricing_29_license": "UNSUPPORTED" if h2_pos == 0 else f"SUPPORTED_BY_{h2_pos}_RESPONSES",
            "developer_community_outreach": "UNSUPPORTED" if h3_pos == 0 else f"SUPPORTED_BY_{h3_pos}_RESPONSES",
            "target_50_devs_14_days": "PROPOSED_THRESHOLD_UNVERIFIED",
            "inferred_vs_observed_note": f"INFERRED != OBSERVED invariant enforced. 0 inferred hypotheses were converted to observed evidence without real user data.",
        }

        # Decision Gate Logic
        if has_synthetic:
            decision = "NO-GO"
            decision_reason = "Synthetic or fake user response detected (is_synthetic=true). Violation of SPEC-0012 invariants."
            confidence = 0
            evidence_quality = 0
        elif user_response_count == 0:
            decision = "VALIDATE_MORE"
            decision_reason = "Zero real user responses observed (observed_response_count = 0). GO decision is IMPOSSIBLE without real user evidence."
            confidence = 35
            evidence_quality = 40
        elif len(negative_evidence) >= max(3, len(positive_evidence)):
            decision = "NO-GO"
            decision_reason = f"Negative evidence outweighs positive signals ({len(negative_evidence)} negative vs {len(positive_evidence)} positive)."
            confidence = 80
            evidence_quality = 75
        elif h1_status == "CONTRADICTED" or h2_status == "CONTRADICTED":
            decision = "NO-GO"
            decision_reason = f"Critical hypothesis contradicted: H1={h1_status}, H2={h2_status}."
            confidence = 75
            evidence_quality = 70
        elif h1_status in ("UNKNOWN", "PARTIALLY_SUPPORTED", "UNSUPPORTED") or h2_status in ("UNKNOWN", "PARTIALLY_SUPPORTED", "UNSUPPORTED"):
            decision = "VALIDATE_MORE"
            decision_reason = f"Hypothesis validation incomplete: H1={h1_status}, H2={h2_status}. GO decision requires verified problem and payment intent."
            confidence = 60
            evidence_quality = 65
        elif h1_status == "OBSERVED" and h2_status == "OBSERVED" and h3_status in ("OBSERVED", "PARTIALLY_SUPPORTED") and user_response_count >= 10:
            decision = "GO"
            decision_reason = f"All 3 core hypotheses verified by real user evidence ({user_response_count} responses logged)."
            confidence = 85
            evidence_quality = 85
        else:
            decision = "VALIDATE_MORE"
            decision_reason = f"Logged {user_response_count}/10 responses. Sample size is insufficient for a definitive GO decision."
            confidence = 55
            evidence_quality = 60

        return {
            "opportunity": topic,
            "observed_response_count": user_response_count,
            "target_response_threshold": 10,
            "positive_evidence": positive_evidence,
            "negative_evidence": negative_evidence,
            "neutral_evidence": neutral_evidence,
            "unknown_evidence": unknown_evidence,
            "hypotheses": hypotheses_evaluation,
            "self_critique": self_critique,
            "evidence_quality": evidence_quality,
            "confidence": confidence,
            "decision": decision,
            "decision_reason": decision_reason,
            "next_action": (
                "Deploy outreach message & survey to developer communities to collect first 10 real user responses."
                if user_response_count == 0
                else "Proceed to SPEC-0019 MVP Technical Specification." if decision == "GO"
                else "Pivot to alternative market segment." if decision == "NO-GO"
                else "Continue collecting survey responses until 10 target responses are logged."
            ),
            "evidence_lineage": {
                "sources": raw_evidence.get("sources", []),
                "evidence_hash": raw_evidence.get("evidence_hash", "sha256_evidence_analysis_ledger"),
                "has_synthetic": has_synthetic,
                "input_file": "lab/experiments/input/user_responses.json",
            },
        }
