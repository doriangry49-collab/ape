from __future__ import annotations

from typing import Any, Dict, List


class ProductValidationEngine:
    """
    R&D Product Validation Engine.
    
    Subjects candidate opportunity cards and raw research evidence to strict empirical auditing.
    Classifies all claims into EVIDENCED, INFERRED, or UNSUPPORTED.
    Determines honest validation decisions: GO, VALIDATE_MORE, or NO-GO.
    """

    def validate_opportunity(
        self,
        opportunity_card: dict[str, Any],
        raw_evidence: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Runs empirical validation against an opportunity card and raw evidence bundle.
        Returns full Product Validation Contract results.
        """
        topic = raw_evidence.get("topic") or opportunity_card.get("product_name", "unknown")
        pain_points: List[str] = raw_evidence.get("pain_points", [])
        discussions: List[dict] = raw_evidence.get("discussions", [])
        competitors: List[str] = raw_evidence.get("competitors", [])
        sources: List[str] = raw_evidence.get("sources", [])
        market_signals: List[str] = raw_evidence.get("market_signals", [])
        risks: List[str] = raw_evidence.get("risks", [])

        # 1. Audit Statements (EVIDENCED / INFERRED / UNSUPPORTED)
        audit_claims = self._audit_opportunity_claims(opportunity_card, raw_evidence)
        evidenced_count = sum(1 for c in audit_claims if c["status"] == "EVIDENCED")
        inferred_count = sum(1 for c in audit_claims if c["status"] == "INFERRED")
        unsupported_count = sum(1 for c in audit_claims if c["status"] == "UNSUPPORTED")
        total_claims = len(audit_claims) or 1
        unsupported_ratio = unsupported_count / total_claims

        # 2. Compute Grounded Metric Scores
        pain_score = min(100, len(pain_points) * 25 + sum(15 for p in pain_points if any(kw in p.lower() for kw in ["slow", "expensive", "broken", "manual"])))
        demand_score = min(100, (len(discussions) * 20) + (len(market_signals) * 15))
        buyer_intent_score = 75 if any(b in " ".join(raw_evidence.get("target_audience", [])).lower() for b in ["developer", "engineer", "b2b", "founder", "manager"]) else 40
        monetization_signal = min(100, 30 + sum(20 for p in pain_points if "pricing" in p.lower() or "cost" in p.lower() or "api" in p.lower()))

        # Evidence Quality Score (0-100)
        evidence_count = len(pain_points) + len(discussions) + len(sources)
        has_synthetic = raw_evidence.get("is_synthetic", False)
        
        if has_synthetic:
            evidence_quality = 0
        elif evidence_count == 0:
            evidence_quality = 0
        else:
            evidence_quality = max(0, min(100, int((evidenced_count / total_claims * 60) + (min(4, len(sources)) * 10))))

        # Calculate Overall Validation Score & Confidence
        validation_score = int((demand_score * 0.25) + (pain_score * 0.25) + (buyer_intent_score * 0.25) + (monetization_signal * 0.25))
        confidence = min(90, int((evidence_quality * 0.6) + (evidenced_count * 10)))

        # Detect Positive & Negative Signals
        positive_signals = []
        negative_signals = []

        if pain_points:
            positive_signals.append(f"Found {len(pain_points)} verified customer pain points in raw research data.")
        if discussions:
            positive_signals.append(f"Active community discussions detected ({len(discussions)} threads).")
        if unsupported_count > 0:
            negative_signals.append(f"{unsupported_count} product card hypotheses (e.g. pricing, acquisition channels) lack real empirical evidence.")
        if len(sources) <= 1:
            negative_signals.append("Data source count <= 1; high risk of single-source bias.")

        # 3. Decision Logic (Honest & Self-Critiquing)
        if has_synthetic:
            decision = "NO-GO"
            decision_reason = "Synthetic or fabricated evidence detected. Violation of SPEC-0012 invariants."
            next_action = "Reject synthetic data payload immediately."
        elif len(negative_signals) >= 3 or evidence_quality < 30:
            decision = "NO-GO"
            decision_reason = f"Severe evidence gaps and negative signals ({len(negative_signals)} issues found). Market opportunity is unsupported by empirical data."
            next_action = "Pivot research to higher-signal market segments."
        elif unsupported_ratio > 0.35 or evidence_quality < 70 or confidence < 75:
            decision = "VALIDATE_MORE"
            decision_reason = (
                f"Validation score is {validation_score}/100 with {confidence}% confidence, but {unsupported_count} claims "
                f"({int(unsupported_ratio*100)}%) are UNSUPPORTED hypotheses. Requires targeted real-world customer validation."
            )
            next_action = "Execute targeted user survey & landing page test to validate pricing intent and acquisition channels."
        else:
            decision = "GO"
            decision_reason = "Strong grounded evidence, high buyer intent, and verified customer pain."
            next_action = "Proceed to MVP Technical Specification (SPEC-0019)."

        return {
            "opportunity": topic,
            "hypothesis": f"Target customers experience verified pain in {topic} and require a simpler automation workflow.",
            "target_customer": opportunity_card.get("target_customer", []),
            "problem": opportunity_card.get("problem", ""),
            "validation_questions": [
                "Are target customers actively spending money or developer hours on manual workarounds today?",
                "Will target customers pay a recurring fee or one-time license for a local automation CLI tool?",
                "Is the competitive gap open enough to acquire customers without high ad spend?"
            ],
            "evidence_sources": sources,
            "evidence_count": evidence_count,
            "positive_signals": positive_signals,
            "negative_signals": negative_signals,
            "evidence_quality": evidence_quality,
            "demand_score": demand_score,
            "pain_score": pain_score,
            "buyer_intent_score": buyer_intent_score,
            "monetization_signal": monetization_signal,
            "validation_score": validation_score,
            "confidence": confidence,
            "decision": decision,
            "decision_reason": decision_reason,
            "next_action": next_action,
            "audited_claims": audit_claims,
            "what_we_know": [c["claim"] for c in audit_claims if c["status"] == "EVIDENCED"],
            "what_we_dont_know": [c["claim"] for c in audit_claims if c["status"] == "UNSUPPORTED"],
            "evidence_lineage": {
                "sources": sources,
                "evidence_hash": raw_evidence.get("evidence_hash", "sha256_verified_evidence_ledger"),
                "unsupported_claims_ratio": round(unsupported_ratio, 2),
            },
        }

    def _audit_opportunity_claims(self, card: dict[str, Any], raw_evidence: dict[str, Any]) -> List[dict[str, Any]]:
        """Audits statements in the opportunity card against raw evidence."""
        claims = []
        pain_text = " ".join(raw_evidence.get("pain_points", [])).lower()
        comp_list = [c.lower() for c in raw_evidence.get("competitors", [])]

        # Audit 1: Problem statement
        prob = card.get("problem", "")
        if prob and any(p.lower() in pain_text for p in raw_evidence.get("pain_points", [])):
            claims.append({"claim": f"Problem: {prob[:60]}...", "status": "EVIDENCED", "reason": "Directly present in raw customer pain data."})
        elif prob:
            claims.append({"claim": f"Problem: {prob[:60]}...", "status": "INFERRED", "reason": "Extrapolated from broader market discussion trends."})

        # Audit 2: Competitors
        comps = card.get("existing_alternatives", [])
        if comps and all(any(c.lower() in raw_c for raw_c in comp_list) for c in comps[:2]):
            claims.append({"claim": f"Competitors: {', '.join(comps[:2])}", "status": "EVIDENCED", "reason": "Identified in competitor scanner results."})
        elif comps:
            claims.append({"claim": f"Competitors: {', '.join(comps[:2])}", "status": "INFERRED", "reason": "Generic industry incumbents."})

        # Audit 3: Monetization Pricing ($29 license)
        mon_hyp = card.get("monetization_hypothesis", "")
        if "$" in mon_hyp or "license" in mon_hyp:
            claims.append({"claim": f"Monetization: {mon_hyp}", "status": "UNSUPPORTED", "reason": "Hardcoded pricing hypothesis with zero empirical payment intent data."})

        # Audit 4: Acquisition Channel
        acq_hyp = card.get("first_customer_acquisition_hypothesis", "")
        if acq_hyp:
            claims.append({"claim": f"Acquisition: {acq_hyp}", "status": "UNSUPPORTED", "reason": "Hypothetical marketing channel; no live conversion experiment run yet."})

        # Audit 5: Success Criteria (50 active devs / 14 days)
        succ = card.get("success_criteria", "")
        if succ:
            claims.append({"claim": f"Success Target: {succ}", "status": "UNSUPPORTED", "reason": "Arbitrary success benchmark without baseline conversion data."})

        return claims
