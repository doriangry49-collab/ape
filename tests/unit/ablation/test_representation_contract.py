"""Unit Tests for ORION G3b.3a Representation Contract & Isolation Invariants (Refined).

Enforces:
1. Observable 0-4 Rubric rules & criteria consistency.
2. Per-feature explicit allowed/forbidden input field scopes.
3. Dual Static AST + Runtime Target Isolation (human_expert_decision & outcome mutation = 0 effect).
4. Holdout dataset protection guard.
5. Outcome-agnostic pre-locked R2 -> Scorer v1 mapping determinism.
"""

import copy
import pytest
from pathlib import Path

from ape.intelligence.ablation.representation_contract import (
    FeatureRubricLevel,
    FeatureRubric,
    R2Representation,
    RepresentationContract,
    TargetIsolationViolationError,
    HoldoutAccessViolationError,
    RUBRIC_PAIN_DEPTH,
    RUBRIC_DEMAND_INTENSITY,
    RUBRIC_DISCUSSION_ENGAGEMENT,
    RUBRIC_COMMERCIAL_INTENT,
    GLOBAL_ALLOWED_FIELDS,
    GLOBAL_FORBIDDEN_FIELDS,
    extract_r2_features_isolated,
    map_r2_to_scorer_v1_input,
    assert_holdout_protection,
    verify_static_target_isolation,
)
from ape.intelligence.decision.scorer import Scorer, load_weights


@pytest.fixture
def sample_opportunity_record():
    return {
        "opportunity_id": "CALIB-OPP-2026-001",
        "prompt_topic": "B2B AI Code Review Automation",
        "decision_timestamp": "2026-06-01T10:00:00Z",
        "human_expert_decision": "WAIT_FOR_SIGNAL",
        "outcome": {
            "actual_market_outcome": "SUCCESS",
            "outcome_observed_at": "2026-08-01T10:00:00Z",
            "outcome_source": "crunchbase",
            "outcome_confidence": 0.95,
            "provenance_details": "Acquired by BigTech",
        },
        "evidence_snapshots": [
            {
                "source": "hackernews",
                "source_type": "post",
                "observed_at": "2026-05-15T12:00:00Z",
                "available_at": "2026-05-15T12:00:00Z",
                "reference": "HN-99812",
                "content_hash": "hash_val_1",
                "raw_observation": "Pain point: Developers struggling with manual pull request reviews, huge issue in team.",
            },
            {
                "source": "reddit",
                "source_type": "thread",
                "observed_at": "2026-05-20T14:00:00Z",
                "available_at": "2026-05-20T14:00:00Z",
                "reference": "RED-4412",
                "content_hash": "hash_val_2",
                "raw_observation": "Active discussion thread with 10+ comments. Users asking if they can pay for pre-order solution.",
            },
            {
                "source": "twitter",
                "source_type": "tweet",
                "observed_at": "2026-05-25T09:00:00Z",
                "available_at": "2026-05-25T09:00:00Z",
                "reference": "TW-7711",
                "content_hash": "hash_val_3",
                "raw_observation": "Inquiring about pricing and enterprise subscription plans for code review assistant.",
            },
        ],
    }


def test_observable_rubric_definitions_and_bounds():
    """Verify observable rubric criteria and boundary checks."""
    assert RUBRIC_PAIN_DEPTH.validate_level(0) == FeatureRubricLevel.NONE
    assert RUBRIC_PAIN_DEPTH.validate_level(4) == FeatureRubricLevel.EXCEPTIONAL

    with pytest.raises(ValueError):
        RUBRIC_PAIN_DEPTH.validate_level(5)

    assert len(RUBRIC_PAIN_DEPTH.criteria_rules) == 5
    assert "keyword matches" in RUBRIC_PAIN_DEPTH.criteria_rules[FeatureRubricLevel.NONE]
    assert "0 observable" in RUBRIC_PAIN_DEPTH.criteria_rules[FeatureRubricLevel.NONE]


def test_per_feature_input_scopes():
    """Verify explicit allowed and forbidden input field scopes for every feature (§2)."""
    for rubric in (RUBRIC_PAIN_DEPTH, RUBRIC_DEMAND_INTENSITY, RUBRIC_DISCUSSION_ENGAGEMENT, RUBRIC_COMMERCIAL_INTENT):
        assert rubric.input_scope.allowed_fields == GLOBAL_ALLOWED_FIELDS
        assert "human_expert_decision" in rubric.input_scope.forbidden_fields
        assert "actual_market_outcome" in rubric.input_scope.forbidden_fields


def test_static_ast_target_isolation():
    """Verify static AST inspection confirms feature extraction contains no target references (§3)."""
    # Should complete with zero errors
    verify_static_target_isolation(extract_r2_features_isolated)

    # Verify AST check catches illegal function accessing forbidden target fields
    def illegal_extractor(record):
        return record.get("human_expert_decision")

    with pytest.raises(TargetIsolationViolationError):
        verify_static_target_isolation(illegal_extractor)


def test_target_isolation_invariant(sample_opportunity_record):
    """Enforces that mutating human_expert_decision or outcome MUST NOT alter R2 features or Scorer v1 output (§3)."""
    project_root = Path(__file__).resolve().parents[3]
    weights = load_weights(project_root)
    scorer = Scorer(weights)

    # 1. Baseline R2 extraction and mapping
    r2_baseline = extract_r2_features_isolated(sample_opportunity_record)
    scorer_input_baseline = map_r2_to_scorer_v1_input(r2_baseline, sample_opportunity_record["prompt_topic"])
    score_baseline, vector_baseline, decision_baseline = scorer.score(scorer_input_baseline)

    # 2. Mutate human_expert_decision label from WAIT_FOR_SIGNAL to BUILD
    record_mutated_decision = copy.deepcopy(sample_opportunity_record)
    record_mutated_decision["human_expert_decision"] = "BUILD"

    r2_mutated_dec = extract_r2_features_isolated(record_mutated_decision)
    scorer_input_mutated_dec = map_r2_to_scorer_v1_input(r2_mutated_dec, record_mutated_decision["prompt_topic"])
    score_mutated_dec, _, decision_mutated_dec = scorer.score(scorer_input_mutated_dec)

    assert r2_baseline == r2_mutated_dec, "TARGET LEAKAGE DETECTED: R2 representation changed upon human_expert_decision mutation!"
    assert score_baseline == score_mutated_dec, "TARGET LEAKAGE DETECTED: Score changed upon human_expert_decision mutation!"

    # 3. Mutate actual_market_outcome label from SUCCESS to FAILED
    record_mutated_outcome = copy.deepcopy(sample_opportunity_record)
    record_mutated_outcome["outcome"]["actual_market_outcome"] = "FAILED"

    r2_mutated_out = extract_r2_features_isolated(record_mutated_outcome)
    scorer_input_mutated_out = map_r2_to_scorer_v1_input(r2_mutated_out, record_mutated_outcome["prompt_topic"])
    score_mutated_out, _, decision_mutated_out = scorer.score(scorer_input_mutated_out)

    assert r2_baseline == r2_mutated_out, "TARGET LEAKAGE DETECTED: R2 representation changed upon outcome mutation!"
    assert score_baseline == score_mutated_out, "TARGET LEAKAGE DETECTED: Score changed upon outcome mutation!"


def test_holdout_protection_invariant(tmp_path):
    """Verify that attempting to access the holdout file raises HoldoutAccessViolationError (§3)."""
    holdout_file = tmp_path / "locked_holdout_dataset.json"
    holdout_file.write_text("{}")

    dev_file = tmp_path / "calibration_dev_dataset.json"
    dev_file.write_text("{}")

    # Accessing dev file should pass
    assert_holdout_protection(dev_file, holdout_file)

    # Accessing holdout file should raise error
    with pytest.raises(HoldoutAccessViolationError):
        assert_holdout_protection(holdout_file, holdout_file)


def test_r2_vector_and_mapping_determinism(sample_opportunity_record):
    """Verify R2 vector generation and Scorer v1 mapping determinism (§4)."""
    r2 = extract_r2_features_isolated(sample_opportunity_record)
    vec = r2.to_vector()

    assert len(vec) == 4
    assert all(0 <= v <= 4 for v in vec)

    mapped_input = map_r2_to_scorer_v1_input(r2, sample_opportunity_record["prompt_topic"])
    assert "pain_points" in mapped_input
    assert "discussions" in mapped_input
    assert "risks" in mapped_input
    assert "competitors" in mapped_input
    assert "target_audience" in mapped_input


def test_contract_hypotheses_and_metrics_lock():
    """Verify contract freeze metadata and pre-registered hypotheses (§4)."""
    contract = RepresentationContract()
    assert contract.contract_version == "G3b.3a-FREEZE-2.0-REFINED"
    assert "without tuning" in contract.mapping_objective
    assert "BUILD_count" in contract.locked_metrics
    assert "score_mean" in contract.locked_metrics
    assert len(contract.locked_metrics) == 10
