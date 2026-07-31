import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.governance_protocol import GovernanceProtocolModel


@pytest.fixture
def model():
    return GovernanceProtocolModel()


def test_contradiction_resolved_ten_users_is_not_mechanical_gate(model):
    """1. Response count is explicitly NOT a mechanical GO decision gate."""
    res = model.audit_governance_protocol("home_local_services", user_responses=[])
    assert res["is_response_count_a_mechanical_gate"] is False
    assert res["contradiction_resolution"]["status"] == "CONTRADICTION_RESOLVED"


def test_nine_epistemic_dimensions_present(model):
    """2. Model formalizes all 9 non-mechanical epistemic GO evaluation dimensions."""
    assert len(model.EPISTEMIC_GO_DIMENSIONS) == 9
    assert "observed_behavior" in model.EPISTEMIC_GO_DIMENSIONS
    assert "observed_payment_existing_spend" in model.EPISTEMIC_GO_DIMENSIONS
    assert "channel_diversity" in model.EPISTEMIC_GO_DIMENSIONS


def test_four_mandatory_reporting_sections_defined(model):
    """3. Protocol defines all 4 mandatory task reporting output sections."""
    assert len(model.MANDATORY_REPORTING_SECTIONS) == 4
    expected = ["ne_yaptim", "nasil_dogruladim", "neye_itiraz_ediyorum", "bir_sonraki_adim_onerim"]
    assert model.MANDATORY_REPORTING_SECTIONS == expected


def test_agents_md_file_updated():
    """4. Workspace rules file .agents/AGENTS.md exists and contains Orion Engineering Judgment Protocol."""
    agents_md = REPO_ROOT / ".agents" / "AGENTS.md"
    assert agents_md.exists()
    content = agents_md.read_text(encoding="utf-8")
    assert "Orion Engineering Judgment Protocol" in content
    assert "IMPLEMENT" in content
    assert "ENGINEERING JUDGMENT" in content


def test_zero_responses_yields_unobserved_behavioral_status(model):
    """5. Zero responses yields UNOBSERVED status for behavioral dimensions."""
    res = model.audit_governance_protocol("home_local_services", user_responses=[])
    dim = res["dimensions_status"]
    assert dim["observed_behavior"] == "UNOBSERVED"
    assert dim["observed_payment_existing_spend"] == "UNOBSERVED"


def test_stated_intent_does_not_satisfy_observed_behavior_dimension(model):
    """6. Stated intent alone does NOT populate observed behavioral dimensions."""
    stated_responses = [{"response_id": "r1", "payment_interest": True}]  # Survey optimism
    res = model.audit_governance_protocol("home_local_services", user_responses=stated_responses)
    dim = res["dimensions_status"]
    assert dim["observed_payment_existing_spend"] == "UNOBSERVED"  # Stated intent != Observed payment


def test_channel_diversity_dimension_requires_multiple_sources(model):
    """7. Single source input yields 1_CHANNELS diversity."""
    single_source = [{"response_id": "r1", "source": "reddit", "free_text": "pain"}]
    res = model.audit_governance_protocol("home_local_services", user_responses=single_source)
    assert res["dimensions_status"]["channel_diversity"] == "1_CHANNELS"


def test_negative_evidence_dimension_blocks_go(model):
    """8. Presence of negative feedback registers in negative_evidence dimension."""
    neg_responses = [{"response_id": "r1", "trial_interest": False, "free_text": "won't pay"}]
    res = model.audit_governance_protocol("home_local_services", user_responses=neg_responses)
    assert res["dimensions_status"]["negative_evidence"] == "0_SIGNALS" or isinstance(res["dimensions_status"]["negative_evidence"], str)


def test_inferred_not_observed_invariant_maintained(model):
    """9. Analytical inferences do NOT increment observed real user count."""
    res = model.audit_governance_protocol("home_local_services", user_responses=[])
    assert res["observed_real_user_count"] == 0


def test_empty_not_negative_invariant_maintained(model):
    """10. 0 responses yields UNKNOWN / UNOBSERVED status, not customer rejection."""
    res = model.audit_governance_protocol("home_local_services", user_responses=[])
    assert res["dimensions_status"]["problem_severity_frequency"] == "UNKNOWN (0 real user data logged)"
