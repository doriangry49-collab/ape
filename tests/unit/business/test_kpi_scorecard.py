"""
Unit tests for KPI & Scorecard Engine (Phase B2).
"""

import pytest

from ape.business.scorecard import BusinessScorecardEngine, OrganizationalScorecard
from ape.business.units import EngineeringUnit, QAUnit


def test_business_scorecard_computation():
    engine = BusinessScorecardEngine()
    eng_unit = EngineeringUnit()

    rep = eng_unit.execute(None)
    scorecard = engine.compute_scorecard([rep])

    assert isinstance(scorecard, OrganizationalScorecard)
    assert scorecard.engineering_velocity == 94.5
    assert scorecard.to_dict()["overall_health_score"] > 0
