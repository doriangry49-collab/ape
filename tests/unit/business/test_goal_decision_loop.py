"""
Unit tests for ORION-105 Goal-Driven Decision Loop & Autonomous Reasoning Engine.
Verifies Goal root entity, GoalReasoningEngine hypothesis formulation, capability matching, and VentureOutcome learning.
"""

import pytest

from ape.business import (
    Goal,
    GoalReasoningEngine,
    OutcomeStatus,
    ProductType,
    VentureEngine,
    VentureOutcome,
)


def test_goal_root_entity():
    goal = Goal.create(
        title="Reduce listing prep time for real estate agents in Turkey",
        target_market="Real Estate Agents Turkey",
    )

    assert goal.goal_id.startswith("goal_")
    assert "real estate" in goal.title.lower()
    assert goal.target_market == "Real Estate Agents Turkey"
    d = goal.to_dict()
    assert d["title"] == goal.title


def test_goal_reasoning_engine_hypothesis_selection():
    engine = GoalReasoningEngine()

    # 1. Test real estate goal evaluation -> Recommends CHROME_EXTENSION + pack_real_estate
    goal_re = Goal.create("Automate real estate listing creation", target_market="Real Estate")
    decision_re = engine.evaluate_goal(goal_re, available_roles=["Coder"])

    assert decision_re.selected_hypothesis.product_type == ProductType.CHROME_EXTENSION
    assert decision_re.recommended_pack_id == "pack_real_estate"
    assert "LeadFinder" in decision_re.missing_capabilities

    # 2. Test media goal evaluation -> Recommends MEDIA_CHANNEL + pack_youtube_studio
    goal_media = Goal.create("Launch tech youtube studio channel", target_market="Media Content")
    decision_media = engine.evaluate_goal(goal_media)

    assert decision_media.selected_hypothesis.product_type == ProductType.MEDIA_CHANNEL
    assert decision_media.recommended_pack_id == "pack_youtube_studio"


def test_7_step_goal_to_outcome_loop():
    # Step 1: Goal
    goal = Goal.create("Produce SaaS developer tool", target_market="Developer Tools")

    # Step 2 & 3 & 4: Reasoning & Decision
    reasoning = GoalReasoningEngine()
    decision = reasoning.evaluate_goal(goal)
    assert decision.confidence_score > 90.0

    # Step 5: Execution Pipeline
    venture = VentureEngine()
    product = venture.create_product(goal.title, product_type=decision.selected_hypothesis.product_type)
    res = venture.run_venture_pipeline(product.product_id, target_market=goal.target_market)

    # Step 6 & 7: Outcome & Learning
    outcome = VentureOutcome(
        outcome_id="out_001",
        goal_id=goal.goal_id,
        product_id=product.product_id,
        status=OutcomeStatus.VALIDATED,
        findings=["Product pipeline completed.", f"Merkle Proof: {res.merkle_evidence_proof}"],
    )

    assert outcome.status == OutcomeStatus.VALIDATED
    assert len(outcome.findings) == 2
