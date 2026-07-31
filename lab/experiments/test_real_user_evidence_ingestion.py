import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.real_user_evidence_ingestion import RealUserEvidenceIngestionValidator
from lab.candidates.real_user_evidence_analysis import RealUserEvidenceAnalyzer


@pytest.fixture
def validator():
    return RealUserEvidenceIngestionValidator()


@pytest.fixture
def analyzer():
    return RealUserEvidenceAnalyzer()


def test_empty_input_remains_validate_more(validator, analyzer):
    """1. Empty input ([] user responses) remains VALIDATE_MORE and 0 observed responses."""
    clean, errors = validator.validate_responses([])
    assert len(clean) == 0
    assert len(errors) == 0

    res = analyzer.analyze_evidence("home_local_services", {"topic": "home_local_services"}, clean)
    assert res["decision"] == "VALIDATE_MORE"
    assert res["observed_response_count"] == 0


def test_missing_optional_fields_become_unknown(validator):
    """2. Incomplete survey responses are accepted; missing optional fields become None / UNKNOWN."""
    raw = [
        {
            "response_id": "r1",
            "source": "reddit",
            "free_text": "Manual setup is slow",
            # problem_frequency, trial_interest, payment_interest omitted
        }
    ]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 1
    assert clean[0]["problem_frequency"] is None
    assert clean[0]["trial_interest"] is None


def test_pii_fields_rejected(validator):
    """3. Presence of forbidden PII fields (email, name, phone) triggers ingestion rejection."""
    raw = [
        {
            "response_id": "r1",
            "source": "reddit",
            "email": "user@example.com",
            "free_text": "Setup is hard",
        }
    ]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0
    assert len(errors) == 1
    assert "forbidden PII field" in errors[0]


def test_is_synthetic_true_rejected(validator):
    """4. Synthetic payloads (is_synthetic: True) are rejected by the ingestion gate."""
    raw = [
        {
            "response_id": "bot_1",
            "source": "reddit",
            "is_synthetic": True,
            "free_text": "Fabricated survey feedback",
        }
    ]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0
    assert len(errors) == 1
    assert "synthetic data payload" in errors[0]


def test_duplicate_response_id_rejected(validator):
    """5. Duplicate response_id entries are rejected."""
    raw = [
        {"response_id": "r1", "source": "reddit", "free_text": "First response"},
        {"response_id": "r1", "source": "reddit", "free_text": "Duplicate response"},
    ]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 1
    assert len(errors) == 1
    assert "duplicate response_id" in errors[0]


def test_invalid_source_becomes_unknown(validator):
    """6. Invalid or unrecognized source string is normalized to UNKNOWN."""
    raw = [
        {"response_id": "r1", "source": "invalid_random_forum", "free_text": "Setup pain"}
    ]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 1
    assert clean[0]["source"] == "UNKNOWN"


def test_previous_ape_report_content_cannot_be_treated_as_observed_evidence(analyzer):
    """7. Copied content from previous APE reports cannot raise observed_response_count."""
    raw_evidence = {"topic": "home_local_services", "sources": ["HN"]}
    res = analyzer.analyze_evidence("home_local_services", raw_evidence, user_responses=[])
    # Analytical hypotheses from previous reports remain UNSUPPORTED / UNKNOWN
    crit = res["self_critique"]
    assert crit["pricing_29_license"] == "UNSUPPORTED"
    assert res["observed_response_count"] == 0


def test_blank_response_cannot_become_evidence(validator):
    """8. Completely blank response record (no text, no survey fields) is rejected."""
    raw = [{"response_id": "blank_1"}]
    clean, errors = validator.validate_responses(raw)
    assert len(clean) == 0
    assert len(errors) == 1
    assert "blank response record" in errors[0]


def test_input_template_contains_zero_real_responses():
    """9. Verification that user_response_template.json is empty [] containing 0 real responses."""
    template_path = REPO_ROOT / "lab" / "experiments" / "input" / "user_response_template.json"
    assert template_path.exists()
    content = json.loads(template_path.read_text(encoding="utf-8"))
    assert isinstance(content, list)
    assert len(content) == 0
