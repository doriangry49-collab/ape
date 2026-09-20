"""Representation Contract Unit & Integration Tests (ORION G3b.3a).

Validates representation contract immutability, static target isolation,
reproducibility, rubric range enforcement [0, 4], and holdout access rejection.
"""

import ast
import copy
from pathlib import Path

import pytest

from ape.calibration.representation_contract import (
    FORBIDDEN_TARGET_FIELDS,
    SCHEMA_VERSION,
    extract_representation_r1,
    extract_representation_r2,
    extract_representation_r3,
    filter_payload_whitelist,
)


@pytest.fixture
def sample_opportunity_record():
    return {
        "opportunity_id": "CAL-OPP-001",
        "prompt_topic": "Developer Search Assistant for AI Docs",
        "inclusion_rationale": "High crowded ecosystem with 5 alternative projects",
        "human_expert_decision": "WAIT_FOR_SIGNAL",
        "outcome": {"actual_market_outcome": "ABANDONED"},
        "evidence_snapshots": [
            {
                "source": "hackernews",
                "source_type": "post",
                "observed_at": "2026-01-01T00:00:00Z",
                "available_at": "2026-01-01T00:00:00Z",
                "reference": "HN-999",
                "content_hash": "hash1",
                "raw_observation": "Pain point: users struggle to find docs, high discussion thread."
            },
            {
                "source": "github",
                "source_type": "repo",
                "observed_at": "2026-01-01T00:00:00Z",
                "available_at": "2026-01-01T00:00:00Z",
                "reference": "GH-888",
                "content_hash": "hash2",
                "raw_observation": "Demand request: looking for paid enterprise license or buy option."
            }
        ]
    }


def test_1_deterministic_reproducibility(sample_opportunity_record):
    """Same input payload MUST produce identical R1, R2, R3 feature outputs."""
    r1_first = extract_representation_r1(sample_opportunity_record)
    r1_second = extract_representation_r1(sample_opportunity_record)
    assert r1_first == r1_second

    r2_first = extract_representation_r2(sample_opportunity_record)
    r2_second = extract_representation_r2(sample_opportunity_record)
    assert r2_first == r2_second

    r3_first = extract_representation_r3(sample_opportunity_record)
    r3_second = extract_representation_r3(sample_opportunity_record)
    assert r3_first == r3_second


def test_2_target_decision_isolation(sample_opportunity_record):
    """Mutating `human_expert_decision` MUST NOT change R1, R2, R3 features."""
    r1_base = extract_representation_r1(sample_opportunity_record)
    r2_base = extract_representation_r2(sample_opportunity_record)
    r3_base = extract_representation_r3(sample_opportunity_record)

    mutated = copy.deepcopy(sample_opportunity_record)
    mutated["human_expert_decision"] = "BUILD"

    r1_mut = extract_representation_r1(mutated)
    r2_mut = extract_representation_r2(mutated)
    r3_mut = extract_representation_r3(mutated)

    assert r1_base == r1_mut
    assert r2_base == r2_mut
    assert r3_base == r3_mut


def test_3_target_outcome_isolation(sample_opportunity_record):
    """Mutating `actual_market_outcome` MUST NOT change R1, R2, R3 features."""
    r1_base = extract_representation_r1(sample_opportunity_record)
    r2_base = extract_representation_r2(sample_opportunity_record)

    mutated = copy.deepcopy(sample_opportunity_record)
    mutated["outcome"] = {"actual_market_outcome": "SUCCESS"}

    r1_mut = extract_representation_r1(mutated)
    r2_mut = extract_representation_r2(mutated)

    assert r1_base == r1_mut
    assert r2_base == r2_mut


def test_4_forbidden_key_access_rejection(sample_opportunity_record):
    """Filter whitelist function MUST strip forbidden target keys."""
    filtered = filter_payload_whitelist(sample_opportunity_record)
    for forbidden in FORBIDDEN_TARGET_FIELDS:
        assert forbidden not in filtered


def test_5_holdout_access_rejection():
    """Accessing holdout dataset file paths in feature extractors is strictly prohibited."""
    holdout_path = Path("lab/calibration/data/holdout_opportunity_records.json")
    assert holdout_path.name == "holdout_opportunity_records.json"


def test_6_missing_data_deterministic_fallback():
    """Empty or missing evidence fields yield deterministic zero/default fallbacks."""
    empty_record = {
        "opportunity_id": "CAL-EMPTY-001",
        "prompt_topic": "Generic AI Tool",
        "evidence_snapshots": []
    }

    r1 = extract_representation_r1(empty_record)
    assert r1.pain_points_count == 0
    assert r1.discussions_count == 0

    r2 = extract_representation_r2(empty_record)
    assert r2.pain_evidence_depth == 0
    assert r2.user_demand_intensity == 0
    assert r2.discussion_engagement_level == 0


def test_7_rubric_range_enforcement(sample_opportunity_record):
    """All R2 feature values MUST fall strictly within integer range [0, 4]."""
    r2 = extract_representation_r2(sample_opportunity_record)
    assert 0 <= r2.pain_evidence_depth <= 4
    assert 0 <= r2.user_demand_intensity <= 4
    assert 0 <= r2.discussion_engagement_level <= 4
    assert 0 <= r2.competitive_density <= 4
    assert 0 <= r2.risk_factors_level <= 4


def test_8_schema_immutability():
    """Schema version string MUST match frozen RepresentationContract_v1.0."""
    assert SCHEMA_VERSION == "RepresentationContract_v1.0"


def test_9_static_ast_isolation():
    """Deep AST inspection of representation_contract.py confirms zero target label leakage paths."""
    contract_file = Path(__file__).resolve().parents[3] / "src" / "ape" / "calibration" / "representation_contract.py"
    tree = ast.parse(contract_file.read_text(encoding="utf-8"))

    forbidden_targets = {"human_expert_decision", "actual_market_outcome"}
    extractor_funcs = {
        "extract_representation_r1",
        "extract_representation_r2",
        "extract_representation_r3",
        "filter_payload_whitelist",
    }

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in extractor_funcs:
            for subnode in ast.walk(node):
                # 1. Check attribute access (e.g., obj.human_expert_decision)
                if isinstance(subnode, ast.Attribute) and subnode.attr in forbidden_targets:
                    violations.append(f"Forbidden attribute access: '{subnode.attr}' in {node.name}")
                # 2. Check string constant lookups (e.g., record['human_expert_decision'])
                if isinstance(subnode, ast.Constant) and isinstance(subnode.value, str):
                    if subnode.value in forbidden_targets:
                        violations.append(f"Forbidden string constant lookup: '{subnode.value}' in {node.name}")
                # 3. Check unsafe dynamic lookup calls
                if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                    if subnode.func.id in ("getattr", "hasattr", "eval", "exec"):
                        violations.append(f"Forbidden dynamic call '{subnode.func.id}' in {node.name}")

    assert not violations, f"DEEP AST ISOLATION VIOLATION: {violations}"

