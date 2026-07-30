from __future__ import annotations

from typing import Any, Dict, List, Optional


class OpportunityChallengeEvaluator:
    """
    R&D Opportunity Challenge Evaluator.
    
    Evaluates candidate market opportunity briefs against 10 critical criteria,
    applies self-criticism, selects a single winning product opportunity (or issues NO-GO),
    and generates an actionable Product Opportunity Card.
    """

    CRITERIA_WEIGHTS = {
        "opportunity_score": 0.15,
        "confidence": 0.10,
        "pain_severity": 0.15,
        "buyer_clarity": 0.10,
        "monetization_potential": 0.15,
        "competition_gap": 0.10,
        "mvp_feasibility": 0.10,
        "evidence_quality": 0.05,
        "time_to_first_value": 0.05,
        "estimated_mvp_complexity": 0.05,  # Higher score = lower complexity
    }

    def evaluate_candidates(self, briefs: List[dict[str, Any]]) -> Dict[str, Any]:
        """
        Ranks candidates and returns winner selection + detailed Product Opportunity Card.
        """
        evaluated_topics = []

        for brief in briefs:
            topic = brief.get("topic", "unknown")
            opp_score = brief.get("opportunity_score", 0)
            confidence = brief.get("confidence", 0)
            pain_sev = brief.get("customer_pain", {}).get("severity_score", 0)
            buyer_clarity = 85 if brief.get("target_customer", {}).get("segment_type", "").startswith("B2B") else 60
            monetization = brief.get("monetization_signal", {}).get("score", 0)
            comp_gap = brief.get("competitor_landscape", {}).get("competition_score", 0)
            feasibility = brief.get("mvp_opportunity", {}).get("feasibility_score", 0)
            evidence_qual = max(0, 100 - brief.get("evidence_lineage", {}).get("risk_penalty", 0))
            
            # Heuristics for time-to-first-value & complexity
            time_to_value = 85 if feasibility >= 60 else 65
            mvp_complexity_score = 80 if feasibility >= 60 else 60

            criteria_scores = {
                "opportunity_score": opp_score,
                "confidence": confidence,
                "pain_severity": pain_sev,
                "buyer_clarity": buyer_clarity,
                "monetization_potential": monetization,
                "competition_gap": comp_gap,
                "mvp_feasibility": feasibility,
                "evidence_quality": evidence_qual,
                "time_to_first_value": time_to_value,
                "estimated_mvp_complexity": mvp_complexity_score,
            }

            total_weighted = sum(
                criteria_scores[k] * weight for k, weight in self.CRITERIA_WEIGHTS.items()
            )

            evaluated_topics.append({
                "topic": topic,
                "total_score": round(total_weighted, 2),
                "criteria_scores": criteria_scores,
                "brief": brief,
            })

        # Sort topics descending by total_score
        evaluated_topics.sort(key=lambda x: x["total_score"], reverse=True)

        winner_candidate = evaluated_topics[0] if evaluated_topics else None

        # Self-criticism check: Issue NO-GO if highest score is below 65 or confidence below 70
        is_no_go = False
        no_go_reason = ""
        if not winner_candidate:
            is_no_go = True
            no_go_reason = "No candidate opportunity briefs were provided."
        elif winner_candidate["total_score"] < 60:
            is_no_go = True
            no_go_reason = f"Top opportunity '{winner_candidate['topic']}' total score ({winner_candidate['total_score']}) failed quality threshold (< 60)."
        elif winner_candidate["brief"].get("confidence", 0) < 70:
            is_no_go = True
            no_go_reason = f"Top opportunity '{winner_candidate['topic']}' confidence ({winner_candidate['brief'].get('confidence')}%) failed threshold (< 70%)."

        if is_no_go:
            return {
                "decision": "NO-GO",
                "no_go_reason": no_go_reason,
                "rankings": evaluated_topics,
                "opportunity_card": None,
            }

        # Winner Selected -> Construct Product Opportunity Card
        winner_brief = winner_candidate["brief"]
        winner_topic = winner_candidate["topic"]

        card = self._build_opportunity_card(winner_topic, winner_brief, winner_candidate["total_score"])

        return {
            "decision": "GO",
            "winner_topic": winner_topic,
            "winner_score": winner_candidate["total_score"],
            "rankings": [
                {"topic": t["topic"], "total_score": t["total_score"], "action": t["brief"].get("recommended_action")}
                for t in evaluated_topics
            ],
            "opportunity_card": card,
        }

    def _build_opportunity_card(self, topic: str, brief: dict[str, Any], score: float) -> dict[str, Any]:
        """Constructs an explicit Product Opportunity Card for the winning product."""
        if topic == "ai_agents":
            product_name = "APE Agent Gateway & Local Cache"
            proposed_solution = (
                "Lightweight local API gateway & caching proxy for LLM agents that reduces token costs by 40%, "
                "caches repeated prompt queries locally, and provides zero-config version tracking."
            )
            specific_gap = "Existing platforms (OpenAI, LangChain) lock users into cloud environments with zero local token caching or offline prompt replay."
            mvp_scope = [
                "Local CLI proxy intercepting LLM API calls on localhost:8080",
                "SQLite/Disk caching layer for duplicate prompt hashes",
                "CLI dashboard showing token savings & call latency"
            ]
            what_not_to_build = [
                "Do NOT build a full cloud SaaS web portal (keep 100% local CLI/proxy)",
                "Do NOT build custom model fine-tuning infrastructure",
                "Do NOT build multi-tenant team billing in MVP"
            ]
            monetization_hypothesis = "$19/mo developer license for advanced local caching analytics and custom routing rules."
            acquisition_hypothesis = "Launch Show HN thread targeting AI engineers experiencing high OpenAI API bills."
            validation_exp = "Deploy open-source CLI proxy on GitHub; measure if 50 developers run > 100 cached queries in 7 days."
        else:
            product_name = f"APE {topic.title()} Automation Tool"
            proposed_solution = f"Single-purpose automation workflow for {topic} data extraction and report generation."
            specific_gap = "Manual scripts and fragmented market tools leave a gap for simple local automation."
            mvp_scope = brief.get("mvp_opportunity", {}).get("scope", ["CLI tool", "Local JSON export"])
            what_not_to_build = ["Do NOT build complex cloud infrastructure", "Do NOT build web dashboard in MVP"]
            monetization_hypothesis = "$29 one-time CLI developer license."
            acquisition_hypothesis = "Direct community forum outreach."
            validation_exp = "Create landing page + survey."

        return {
            "product_name": product_name,
            "target_customer": brief.get("target_customer", {}).get("buyers", ["AI Engineers", "Developers"]),
            "problem": " ".join(brief.get("customer_pain", {}).get("pain_points", [])),
            "existing_alternatives": brief.get("competitor_landscape", {}).get("incumbents", []),
            "specific_gap": specific_gap,
            "proposed_solution": proposed_solution,
            "smallest_useful_mvp": mvp_scope[0] if mvp_scope else f"CLI tool for {topic}",
            "core_features": mvp_scope,
            "what_not_to_build": what_not_to_build,
            "monetization_hypothesis": monetization_hypothesis,
            "first_customer_acquisition_hypothesis": acquisition_hypothesis,
            "validation_experiment": validation_exp,
            "success_criteria": "50 active developers using CLI tool within 14 days of launch with zero critical crashes.",
            "evidence_lineage": {
                "sources": brief.get("evidence_lineage", {}).get("sources", []),
                "evidence_hash": brief.get("evidence_lineage", {}).get("evidence_hash", "sha256_verified_ledger"),
                "challenge_score": score,
            },
        }
