import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.external_collection_gate import ExternalEvidenceCollectionGate
from lab.candidates.real_user_evidence_ingestion import RealUserEvidenceIngestionValidator


@pytest.fixture
def gate():
    return ExternalEvidenceCollectionGate()


@pytest.fixture
def validator():
    return RealUserEvidenceIngestionValidator()


def test_zero_real_user_count_locks_gate_and_stop_rule(gate):
    """1. Zero real user responses locks gate: observed_real_user_count=0, GO_POSSIBLE=False, STOP_RULE active."""
    report = gate.audit_collection_gate("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    assert report["observed_real_user_count"] == 0
    assert report["go_possible"] is False
    assert report["current_decision"] == "VALIDATE_MORE"
    assert report["evidence_collection_status"] == "WAITING_FOR_REAL_USERS"
    assert "APE MUST STOP" in report["stop_rule"]


def test_synthetic_payload_triggers_ingestion_rejection(gate, validator):
    """2. Synthetic payload is rejected and yields NO-GO decision."""
    raw = [{"response_id": "bot_1", "is_synthetic": True, "free_text": "Fake feedback"}]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0

    report = gate.audit_collection_gate("home_local_services", {"topic": "home_local_services", "is_synthetic": True}, [])
    assert report["current_decision"] == "NO-GO"
    assert report["go_possible"] is False


def test_inferred_hypotheses_cannot_increment_real_user_count(gate):
    """3. Analytical inferences from past reports do NOT increment observed_real_user_count."""
    raw_evidence = {
        "topic": "home_local_services",
        "pain_points": ["$29 license target", "50 devs target"],
        "sources": ["ORION-034 Report"]
    }
    report = gate.audit_collection_gate("home_local_services", raw_evidence, user_responses=[])
    assert report["observed_real_user_count"] == 0
    assert "UNSUPPORTED" in report["unsupported_previous_hypotheses"][0]


def test_human_handoff_protocol_included(gate):
    """4. Human Handoff Protocol contains explicit 7-step collection instructions."""
    report = gate.audit_collection_gate("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    handoff = report["human_collection_handoff"]
    assert len(handoff) == 7
    assert "user_responses.json" in handoff[3]


def test_hypothesis_matrix_contains_all_three_hypotheses(gate):
    """5. Hypothesis-to-Evidence Matrix includes H1, H2, and H3 with positive/negative requirements."""
    report = gate.audit_collection_gate("home_local_services", {"topic": "home_local_services"}, user_responses=[])
    matrix = report["hypothesis_matrix"]
    assert "H1_problem_exists" in matrix
    assert "H2_payment_intent" in matrix
    assert "H3_acquisition_trial_intent" in matrix
    assert matrix["H1_problem_exists"]["current_status"] == "UNKNOWN"
