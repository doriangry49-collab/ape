"""
Autonomous Goal Reasoning Engine — ORION-105 Specification.
Evaluates strategic goals, generates product form hypotheses, matches organizational capabilities,
and recommends Marketplace Business Model Packs.
"""

from dataclasses import dataclass, field
import hashlib
from typing import Any, Dict, List, Optional

from ape.business.goal import Goal
from ape.business.product import ProductType
from ape.marketplace.business_packs import BusinessModelPackRegistry


@dataclass
class ProductFormHypothesis:
    """Evaluated product form hypothesis for a strategic Goal."""
    product_type: ProductType
    rationale: str
    suitability_score: float  # 0.0 to 100.0


@dataclass
class ReasoningDecision:
    """Decision output packet from GoalReasoningEngine."""
    goal_id: str
    selected_hypothesis: ProductFormHypothesis
    recommended_pack_id: Optional[str]
    missing_capabilities: List[str]
    confidence_score: float


class GoalReasoningEngine:
    """Autonomous reasoning engine that converts Goals into optimal product decisions."""

    def __init__(self, pack_registry: Optional[BusinessModelPackRegistry] = None) -> None:
        self.pack_registry = pack_registry or BusinessModelPackRegistry()

    def evaluate_goal(self, goal: Goal, available_roles: Optional[List[str]] = None) -> ReasoningDecision:
        """
        Formulate product hypotheses for a Goal, match capabilities,
        and select optimal product form and Marketplace Business Model Pack.
        """
        roles = available_roles or ["Coder", "QA"]

        # 1. Formulate Hypotheses based on target_market & title
        hypotheses = [
            ProductFormHypothesis(
                product_type=ProductType.SAAS,
                rationale="SaaS web app provides maximum recurring value for general business goals.",
                suitability_score=92.5,
            ),
            ProductFormHypothesis(
                product_type=ProductType.CHROME_EXTENSION,
                rationale="Extension reduces workflow friction directly inside browser.",
                suitability_score=85.0,
            ),
        ]

        if "real estate" in goal.title.lower() or "real estate" in goal.target_market.lower():
            selected = ProductFormHypothesis(
                product_type=ProductType.CHROME_EXTENSION,
                rationale="Chrome Extension + WhatsApp Bot provides zero-friction workflow for real estate agents.",
                suitability_score=98.0,
            )
            recommended_pack = "pack_real_estate"
        elif "media" in goal.title.lower() or "youtube" in goal.title.lower():
            selected = ProductFormHypothesis(
                product_type=ProductType.MEDIA_CHANNEL,
                rationale="Autonomous Media Channel is optimal for content reach goals.",
                suitability_score=95.0,
            )
            recommended_pack = "pack_youtube_studio"
        else:
            selected = hypotheses[0]
            recommended_pack = "pack_saas_startup"

        # 2. Inspect capability matching
        missing_capabilities = []
        if recommended_pack:
            pack = self.pack_registry.get_pack(recommended_pack)
            if pack:
                missing_capabilities = [r for r in pack.included_roles if r not in roles]

        return ReasoningDecision(
            goal_id=goal.goal_id,
            selected_hypothesis=selected,
            recommended_pack_id=recommended_pack,
            missing_capabilities=missing_capabilities,
            confidence_score=selected.suitability_score,
        )
