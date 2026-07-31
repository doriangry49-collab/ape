from __future__ import annotations

from typing import Any, Dict, List, Optional


class DemandValidationEngine:
    """
    R&D Real User Demand Validation Engine.
    
    Generates non-manipulative validation packages (Landing Page Spec, 5 Non-Leading Survey Questions,
    Acquisition Plan, Pricing Experiment) and evaluates real observed vs inferred user evidence.
    
    Strict Invariants:
    1. INFERRED != OBSERVED (Inferred hypotheses cannot raise evidence quality or count as real user data).
    2. Zero Synthetic User Responses (Synthetic data is strictly rejected).
    3. Self-Critique Decision Matrix (Returns GO, VALIDATE_MORE, or NO-GO).
    """

    EVIDENCE_CATEGORIES = {
        "OBSERVED",
        "USER_REPORTED",
        "EXTERNAL_SOURCE",
        "INFERRED",
        "PROPOSED_THRESHOLD",
        "UNKNOWN",
    }

    def generate_validation_package(self, opportunity: str, raw_evidence: dict[str, Any]) -> dict[str, Any]:
        """
        Builds the 4-component Demand Validation Experiment Package.
        """
        pain_points = raw_evidence.get("pain_points", [])
        audiences = raw_evidence.get("target_audience", [])

        # 1. Landing Page Spec (Testing tested hypotheses without presenting them as facts)
        landing_page_spec = {
            "headline": f"Automate {opportunity.replace('_', ' ').title()} Workflows with Zero Setup Complexity",
            "subheadline": "Stop wasting developer hours on fragile custom scripts and high API pricing model overhead.",
            "target_user": ", ".join(audiences) if audiences else "Developers & Technical Founders",
            "core_problem": pain_points[0] if pain_points else f"Manual labor and fragile scripts in {opportunity}.",
            "proposed_solution": f"Single-command local CLI proxy for {opportunity} with instant JSON output.",
            "call_to_action": "Join Beta Waitlist / Try Local CLI Alpha",
            "pricing_hypothesis_tested": "$29 one-time CLI license (TESTING HYPOTHESIS ONLY — NOT AN ESTABLISHED PRICE)",
        }

        # 2. 5 Non-Leading User Survey Questions (Behavioral & Willingness to Pay)
        survey_questions = [
            {
                "id": "Q1",
                "question": f"How do you currently handle {opportunity.replace('_', ' ')} data extraction and setup in your projects?",
                "type": "open_ended",
                "purpose": "Measures existing behavior and workaround presence without leading.",
            },
            {
                "id": "Q2",
                "question": "How often do you or your team encounter issues or delay caused by setup complexity?",
                "type": "multiple_choice",
                "options": ["Daily", "Weekly", "Monthly", "Rarely / Never"],
                "purpose": "Measures problem frequency objectively.",
            },
            {
                "id": "Q3",
                "question": "Are you currently paying for any tools, SaaS subscriptions, or developer hours to solve this problem?",
                "type": "multiple_choice",
                "options": ["Yes (SaaS / API Subscription)", "Yes (Custom Developer Hours)", "No (Using Free / Internal Tools)"],
                "purpose": "Measures active commercial spend vs free workaround intent.",
            },
            {
                "id": "Q4",
                "question": "What is the single biggest drawback of your current solution?",
                "type": "open_ended",
                "purpose": "Identifies unaddressed competitor niche gaps.",
            },
            {
                "id": "Q5",
                "question": "If a lightweight local CLI tool solved this with zero setup overhead, would you be open to testing an early alpha?",
                "type": "multiple_choice",
                "options": ["Yes, immediately", "Maybe, depending on docs", "No interest"],
                "purpose": "Measures genuine trial intent.",
            },
        ]

        # 3. Acquisition Experiment Plan
        acquisition_experiment = {
            "channel": "Developer Communities & Focused Subreddits / Show HN",
            "target_audience": audiences or ["Indie Hackers", "Software Developers"],
            "outreach_message": f"Built a lightweight local CLI tool to fix setup overhead in {opportunity}. Looking for 10 alpha testers to give blunt feedback.",
            "call_to_action": "Fill out 2-minute survey / Request Alpha Access",
            "measurement": "Impressions -> Survey Visits -> Survey Completions -> Alpha Trial Opt-ins",
            "success_threshold": "PROPOSED_THRESHOLD: 15% survey completion rate & 10 verified alpha trial opt-ins",
            "failure_threshold": "PROPOSED_THRESHOLD: < 3% survey completion rate or zero trial opt-ins",
        }

        # 4. Pricing Validation & Proposed Thresholds
        pricing_experiment = {
            "tested_hypothesis": "$29 one-time CLI developer license",
            "evidence_status": "UNSUPPORTED",
            "validation_method": "Van Westendorp Price Sensitivity Meter & Current Spend Audit",
            "proposed_success_threshold": "PROPOSED_THRESHOLD: > 40% of survey respondents report paying > $25/mo for current workaround",
        }

        return {
            "landing_page_spec": landing_page_spec,
            "user_survey": survey_questions,
            "acquisition_experiment": acquisition_experiment,
            "pricing_experiment": pricing_experiment,
        }

    def evaluate_demand(
        self,
        opportunity: str,
        raw_evidence: dict[str, Any],
        user_responses: Optional[List[dict[str, Any]]] = None
    ) -> dict[str, Any]:
        """
        Evaluates real user demand and outputs full 16-section Demand Validation Report.
        Strictly enforces INFERRED != OBSERVED.
        """
        validation_pkg = self.generate_validation_package(opportunity, raw_evidence)
        sources = raw_evidence.get("sources", [])
        has_synthetic = raw_evidence.get("is_synthetic", False)

        user_responses = user_responses or []
        user_response_count = len(user_responses)

        # Classify Evidence Items
        evidence_items = []
        
        # 1. Raw Scanner Signals
        for s in sources:
            evidence_items.append({"item": f"Scanner source: {s}", "category": "EXTERNAL_SOURCE"})
        for p in raw_evidence.get("pain_points", []):
            evidence_items.append({"item": f"Market pain point: {p}", "category": "EXTERNAL_SOURCE"})

        # 2. Hypotheses
        evidence_items.append({"item": "Pricing hypothesis: $29 license", "category": "INFERRED"})
        evidence_items.append({"item": "Acquisition hypothesis: Direct community outreach", "category": "INFERRED"})
        evidence_items.append({"item": "Proposed threshold: 50 active devs / 14 days", "category": "PROPOSED_THRESHOLD"})

        # 3. Real User Responses
        for resp in user_responses:
            if resp.get("is_synthetic"):
                has_synthetic = True
            evidence_items.append({"item": f"User survey response: {resp.get('feedback', '')}", "category": "USER_REPORTED"})

        # Counts
        observed_count = sum(1 for e in evidence_items if e["category"] in ("OBSERVED", "USER_REPORTED"))
        inferred_count = sum(1 for e in evidence_items if e["category"] in ("INFERRED", "PROPOSED_THRESHOLD"))

        # Scoring & Confidence Computation
        if has_synthetic:
            decision = "NO-GO"
            decision_reason = "Synthetic or fabricated user evidence detected. Strict violation of SPEC-0012 invariants."
            confidence = 0
            evidence_quality = 0
        elif user_response_count == 0:
            decision = "VALIDATE_MORE"
            decision_reason = (
                "Zero real user responses observed yet (user_response_count = 0). "
                "All pricing, acquisition, and conversion thresholds remain INFERRED hypotheses."
            )
            confidence = 40
            evidence_quality = 45
        else:
            # Evaluate user response sentiment & trial intent
            positive_users = sum(1 for r in user_responses if r.get("commercial_intent", False))
            conversion_rate = positive_users / user_response_count
            
            if conversion_rate >= 0.4 and user_response_count >= 10:
                decision = "GO"
                decision_reason = f"Verified strong commercial intent from {positive_users}/{user_response_count} real user survey responses ({int(conversion_rate*100)}%)."
                confidence = 85
                evidence_quality = 80
            elif conversion_rate < 0.1 and user_response_count >= 5:
                decision = "NO-GO"
                decision_reason = f"Low customer demand and payment intent ({positive_users}/{user_response_count} responses). Market validation failed."
                confidence = 80
                evidence_quality = 75
            else:
                decision = "VALIDATE_MORE"
                decision_reason = f"Moderate initial feedback ({positive_users}/{user_response_count} positive), but sample size is insufficient."
                confidence = 60
                evidence_quality = 60

        return {
            "opportunity": opportunity,
            "original_hypotheses": {
                "pricing": "$29 one-time CLI developer license",
                "acquisition": "Direct community forum outreach",
                "success_target": "50 active developers / 14 days",
            },
            "validation_experiment": validation_pkg,
            "evidence_collected": evidence_items,
            "observed_count": observed_count,
            "inferred_count": inferred_count,
            "observed_vs_inferred_note": f"INFERRED != OBSERVED invariant enforced. {observed_count} observed user signals vs {inferred_count} inferred hypotheses.",
            "decision": decision,
            "decision_reason": decision_reason,
            "confidence": confidence,
            "evidence_quality": evidence_quality,
            "what_we_know": [e["item"] for e in evidence_items if e["category"] in ("EXTERNAL_SOURCE", "OBSERVED", "USER_REPORTED")],
            "what_we_still_dont_know": [
                "Real willingness to pay $29 license (UNKNOWN / NOT YET OBSERVED)",
                "Actual customer acquisition conversion rate (UNKNOWN / NOT YET OBSERVED)",
                "14-day retention rate of local CLI users (UNKNOWN / NOT YET OBSERVED)",
            ],
            "next_action": "Deploy Landing Page Spec & User Survey to 2 developer subreddits to collect first 10 real user responses.",
            "evidence_lineage": {
                "sources": sources,
                "evidence_hash": raw_evidence.get("evidence_hash", "sha256_demand_validation_ledger"),
                "has_synthetic": has_synthetic,
            },
        }
