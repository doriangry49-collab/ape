"""
Unit tests for Declarative Policy Engine (PR-I1).
"""

from pathlib import Path
import pytest

from ape.pipeline.contracts import ExecutionContext, StageResult, StageStatus
from ape.policy.contracts import ReleasePolicy
from ape.policy.engine import PolicyEngine


def test_default_policy_evaluation_success(tmp_path: Path):
    engine = PolicyEngine(tmp_path)

    ctx = ExecutionContext(run_id="r1", topic_slug="test_app")
    prev_results = [
        StageResult(stage_name="verification", status=StageStatus.SUCCESS, output_data={"verification_passed": True}),
        StageResult(stage_name="quality_assurance", status=StageStatus.SUCCESS, output_data={
            "quality_report": {
                "release_confidence": 92.0,
                "quality_profile": "standard",
                "results": [
                    {"validator_name": "runtime", "status": "PASS", "score": 100.0},
                    {"validator_name": "security", "status": "PASS", "score": 100.0},
                ],
            }
        }),
        StageResult(stage_name="task_execution", status=StageStatus.SUCCESS, output_data={"status": "COMPLETED"}),
    ]

    result = engine.evaluate(ctx, prev_results)
    assert result.passed is True
    assert len(result.violations) == 0
    assert "Confidence score (92.0%) meets threshold (85.0%)" in result.passed_rules


def test_policy_evaluation_confidence_violation(tmp_path: Path):
    custom_policy = ReleasePolicy(minimum_confidence=95.0)
    engine = PolicyEngine(tmp_path, policy=custom_policy)

    ctx = ExecutionContext(run_id="r1", topic_slug="test_app")
    prev_results = [
        StageResult(stage_name="verification", status=StageStatus.SUCCESS, output_data={"verification_passed": True}),
        StageResult(stage_name="quality_assurance", status=StageStatus.SUCCESS, output_data={
            "quality_report": {
                "release_confidence": 88.0,
                "results": [],
            }
        }),
        StageResult(stage_name="task_execution", status=StageStatus.SUCCESS, output_data={"status": "COMPLETED"}),
    ]

    result = engine.evaluate(ctx, prev_results)
    assert result.passed is False
    assert any("below minimum policy threshold" in v for v in result.violations)
