"""CONSTITUTIONAL INVARIANT TEST — Target Isolation Guarantee (H-3).

Enforces that modifying `human_expert_decision` or `actual_market_outcome`
in calibration opportunity records MUST NOT alter reconstructed features or scores.
"""

import copy
from pathlib import Path
from typing import Any, Dict

from ape.intelligence.decision.scorer import Scorer, load_weights


def extract_features_clean(record: Dict[str, Any]) -> Dict[str, Any]:
    """Target-label leakage-free feature extraction (Allowed: evidence_snapshots, prompt_topic)."""
    evidence_list = record.get("evidence_snapshots", [])
    prompt_topic = record.get("prompt_topic", "").lower()

    pain_points_count = sum(
        1 for ev in evidence_list
        if "pain point" in ev.get("raw_observation", "").lower() or "pain" in ev.get("raw_observation", "").lower()
    )
    discussions_count = sum(
        1 for ev in evidence_list
        if "discussion" in ev.get("raw_observation", "").lower() or "comments" in ev.get("raw_observation", "").lower()
    )

    competitors_count = 1 if "competitor" in prompt_topic or "alternative" in prompt_topic else 0

    return {
        "pain_points": ["p"] * pain_points_count,
        "discussions": ["d"] * discussions_count,
        "risks": ["r1", "r2", "r3"] if "hardware" in prompt_topic or "robot" in prompt_topic else ["r1", "r2"],
        "competitors": ["c"] * competitors_count,
        "target_audience": ["Audience 1", "Audience 2"]
    }


def test_target_isolation_invariant():
    """Verify that human decision or outcome mutations produce 0 feature or score change."""
    sample_record = {
        "opportunity_id": "TEST-001",
        "prompt_topic": "Test Developer Search AI",
        "human_expert_decision": "WAIT_FOR_SIGNAL",
        "outcome": {"actual_market_outcome": "ABANDONED"},
        "evidence_snapshots": [
            {
                "source": "hackernews",
                "source_type": "post",
                "observed_at": "2026-01-01T00:00:00Z",
                "available_at": "2026-01-01T00:00:00Z",
                "reference": "HN-123",
                "content_hash": "abc",
                "raw_observation": "Pain point: developers struggling with docs search, discussion active."
            }
        ]
    }

    # Project root anchor
    project_root = Path(__file__).resolve().parents[3]
    weights = load_weights(project_root)
    scorer = Scorer(weights)

    # 1. Baseline feature extraction and scoring
    feat_baseline = extract_features_clean(sample_record)
    score_baseline, vector_baseline, _ = scorer.score(feat_baseline)

    # 2. Mutate human_expert_decision to BUILD
    record_mutated_dec = copy.deepcopy(sample_record)
    record_mutated_dec["human_expert_decision"] = "BUILD"
    feat_mutated_dec = extract_features_clean(record_mutated_dec)
    score_mutated_dec, vector_mutated_dec, _ = scorer.score(feat_mutated_dec)

    assert feat_baseline == feat_mutated_dec, "TARGET LEAKAGE DETECTED: Features altered by human decision label!"
    assert score_baseline == score_mutated_dec, "TARGET LEAKAGE DETECTED: Score altered by human decision label!"

    # 3. Mutate actual_market_outcome to SUCCESS
    record_mutated_out = copy.deepcopy(sample_record)
    record_mutated_out["outcome"]["actual_market_outcome"] = "SUCCESS"
    feat_mutated_out = extract_features_clean(record_mutated_out)
    score_mutated_out, vector_mutated_out, _ = scorer.score(feat_mutated_out)

    assert feat_baseline == feat_mutated_out, "TARGET LEAKAGE DETECTED: Features altered by outcome label!"
    assert score_baseline == score_mutated_out, "TARGET LEAKAGE DETECTED: Score altered by outcome label!"
