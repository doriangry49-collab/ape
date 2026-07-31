import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.evidence_taxonomy import EvidenceTaxonomyModel


@pytest.fixture
def model():
    return EvidenceTaxonomyModel()


def test_11_categories_present(model):
    """1. Taxonomy model contains all 11 formalized epistemic categories."""
    assert len(model.CATEGORIES) == 11
    expected = {
        "OBSERVED_BEHAVIOR", "OBSERVED_PAYMENT", "OBSERVED_USAGE",
        "STATED_INTENT", "REPORTED_BEHAVIOR", "NEGATIVE_EVIDENCE",
        "UNKNOWN", "INFERRED", "PROVISIONAL_THRESHOLD", "SYNTHETIC", "TEST_FIXTURE"
    }
    assert set(model.CATEGORIES.keys()) == expected


def test_stated_intent_cannot_trigger_go_alone(model):
    """2. STATED_INTENT has low weight (0.3) and CANNOT trigger GO alone."""
    stated = model.CATEGORIES["STATED_INTENT"]
    assert stated["can_trigger_GO"] is False
    assert stated["epistemic_weight"] == 0.3


def test_observed_behavior_has_high_weight(model):
    """3. OBSERVED_BEHAVIOR has maximum weight (1.0) and CAN trigger GO if corroborated."""
    obs = model.CATEGORIES["OBSERVED_BEHAVIOR"]
    assert obs["can_trigger_GO"] is True
    assert obs["epistemic_weight"] == 1.0


def test_provisional_threshold_has_zero_epistemic_weight(model):
    """4. PROVISIONAL_THRESHOLD has zero epistemic weight (0.0) and CANNOT trigger decisions."""
    prov = model.CATEGORIES["PROVISIONAL_THRESHOLD"]
    assert prov["epistemic_weight"] == 0.0
    assert prov["can_trigger_GO"] is False


def test_synthetic_data_has_zero_weight_and_can_trigger_nogo(model):
    """5. SYNTHETIC has zero weight (0.0) and triggers NO-GO payload rejection."""
    synth = model.CATEGORIES["SYNTHETIC"]
    assert synth["epistemic_weight"] == 0.0
    assert synth["can_trigger_NOGO"] is True


def test_zero_responses_yields_high_epistemic_uncertainty(model):
    """6. 0 real responses yields HIGH epistemic uncertainty and 0% completeness."""
    res = model.evaluate_model("home_local_services", user_responses=[])
    metrics = res["epistemic_metrics"]
    assert metrics["evidence_completeness"] == "0%"
    assert "HIGH" in metrics["epistemic_uncertainty"]
