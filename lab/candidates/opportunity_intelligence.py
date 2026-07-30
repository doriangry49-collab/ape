from __future__ import annotations

from typing import Any, Dict, List, Tuple


class ExperimentalOpportunityScorer:
    """
    R&D Experimental Market Opportunity Intelligence Scorer.
    
    Evaluates 6 rich dimensions beyond array length heuristics:
    1. Customer Pain (Severity, frequency, workaround presence)
    2. Market Signal (Discussion velocity, upvotes, recency)
    3. Competition Gap (Generic vs specialized competitor gaps)
    4. Monetization Potential (Budget intent, B2B/B2C fit, recurring revenue signals)
    5. MVP Feasibility (Technical simplicity, time-to-value)
    6. Risk / Uncertainty (Evidence gaps & signal conflict penalties)
    """

    SEVERITY_KEYWORDS = {"manual", "slow", "expensive", "costly", "broken", "waste", "frustrating", "pricing"}
    MONETIZATION_KEYWORDS = {"pricing", "b2b", "api", "budget", "spend", "cost", "subscription", "recurring", "enterprise"}

    def evaluate_opportunity(self, research_data: dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate research_data against the 6 R&D dimensions.
        Returns a rich dict with dimensional scores, overall score, recommendation, and detailed reasoning.
        """
        pain_points: List[str] = research_data.get("pain_points", [])
        discussions: List[dict] = research_data.get("discussions", [])
        competitors: List[str] = research_data.get("competitors", [])
        audiences: List[str] = research_data.get("target_audience", [])
        market_signals: List[str] = research_data.get("market_signals", [])
        risks: List[str] = research_data.get("risks", [])
        sources: List[str] = research_data.get("sources", [])

        # 1. Customer Pain Dimension (0-100)
        # Analyzes text severity keywords and workaround presence
        pain_text = " ".join(pain_points).lower()
        severity_hits = sum(1 for kw in self.SEVERITY_KEYWORDS if kw in pain_text)
        base_pain = min(60, len(pain_points) * 20)
        pain_score = min(100, base_pain + (severity_hits * 10))

        # 2. Market Signal Dimension (0-100)
        # Evaluates discussion points / upvotes and signal volume
        total_points = sum(d.get("points", 0) for d in discussions if isinstance(d, dict))
        signal_count = len(market_signals) + len(discussions)
        market_score = min(100, (signal_count * 15) + min(40, total_points // 20))

        # 3. Competition Gap Dimension (0-100)
        # Identifies whether market is dominated by generic incumbents vs open niche gaps
        num_comp = len(competitors)
        if num_comp == 0:
            comp_score = 50  # Risk of non-existent market
        elif num_comp <= 3:
            comp_score = 85  # Healthy niche gap opportunity
        elif num_comp <= 5:
            comp_score = 60  # Moderate competition
        else:
            comp_score = 30  # Red ocean market

        # 4. Monetization Potential Dimension (0-100)
        # Evaluates B2B audience signals and explicit budget/pricing keywords
        all_text = (pain_text + " " + " ".join(audiences) + " " + " ".join(market_signals)).lower()
        monetization_hits = sum(1 for kw in self.MONETIZATION_KEYWORDS if kw in all_text)
        is_b2b = any(term in all_text for term in ["developer", "engineer", "b2b", "enterprise", "founder", "manager"])
        
        base_monetization = 50 if is_b2b else 30
        monetization_score = min(100, base_monetization + (monetization_hits * 12))

        # 5. MVP Feasibility Dimension (0-100)
        # Fewer complex risks = higher feasibility for rapid MVP
        risk_penalty = len(risks) * 15
        feasibility_score = max(10, 100 - risk_penalty)

        # 6. Risk / Uncertainty Dimension (Penalty 0-100)
        # Penalizes low evidence sources or complete lack of pain points/discussions
        evidence_gap = 0
        if not pain_points:
            evidence_gap += 30
        if not discussions:
            evidence_gap += 20
        if len(sources) <= 1:
            evidence_gap += 20

        # Weighted Overall Score Calculation
        # Weights: Pain 25%, Market 20%, Comp Gap 15%, Monetization 20%, Feasibility 20%
        weighted_score = (
            (pain_score * 0.25)
            + (market_score * 0.20)
            + (comp_score * 0.15)
            + (monetization_score * 0.20)
            + (feasibility_score * 0.20)
        )
        final_score = max(0, min(100, int(weighted_score - (evidence_gap * 0.3))))

        # Recommendation logic based on holistic multi-vector evaluation
        if evidence_gap >= 40:
            recommendation = "REJECT"
            recommendation_reason = "Insufficient evidence or severe signal gaps."
        elif final_score >= 75 and monetization_score >= 60:
            recommendation = "BUILD"
            recommendation_reason = "High pain, strong market signals, and clear monetization potential."
        elif final_score >= 60:
            recommendation = "VALIDATE"
            recommendation_reason = "Promising signals; requires targeted customer validation."
        else:
            recommendation = "WATCH"
            recommendation_reason = "Weak monetization or high competition saturation."

        return {
            "experimental_score": final_score,
            "recommendation": recommendation,
            "recommendation_reason": recommendation_reason,
            "dimensions": {
                "customer_pain": pain_score,
                "market_signal": market_score,
                "competition_gap": comp_score,
                "monetization_potential": monetization_score,
                "mvp_feasibility": feasibility_score,
                "risk_uncertainty_penalty": evidence_gap,
            },
            "reasoning": [
                f"Customer Pain Score ({pain_score}/100): Found {len(pain_points)} pain points with {severity_hits} severity keywords.",
                f"Market Signal Score ({market_score}/100): Found {signal_count} market signals ({total_points} discussion points).",
                f"Competition Gap Score ({comp_score}/100): Evaluated {num_comp} competitors for niche differentiation.",
                f"Monetization Potential ({monetization_score}/100): Detected {monetization_hits} commercial budget keywords (B2B={is_b2b}).",
                f"MVP Feasibility ({feasibility_score}/100): Evaluated {len(risks)} technical risks.",
                f"Risk Penalty ({evidence_gap} pts): Evidence gap assessment across {len(sources)} data sources.",
            ]
        }
