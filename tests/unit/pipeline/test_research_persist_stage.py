"""Unit tests for SPEC-0018 ResearchPersistStage."""

from ape.pipeline.contracts import PipelineContext, StageStatus
from ape.pipeline.stages.acquisition_execution import AcquisitionExecutionStage
from ape.pipeline.stages.capability_validation import CapabilityValidationStage
from ape.pipeline.stages.evidence_fusion import EvidenceFusionStage
from ape.pipeline.stages.explainability import ExplainabilityStage
from ape.pipeline.stages.research_persist import ResearchPersistStage
from ape.pipeline.stages.research_plan import ResearchPlanStage
from ape.pipeline.stages.source_selection import SourceSelectionStage


def test_research_persist_stage_success(tmp_path):
    plan_stage = ResearchPlanStage()
    select_stage = SourceSelectionStage()
    acq_stage = AcquisitionExecutionStage(offline=True)
    val_stage = CapabilityValidationStage()
    fusion_stage = EvidenceFusionStage()
    explain_stage = ExplainabilityStage()
    persist_stage = ResearchPersistStage(project_root=tmp_path)

    ctx = PipelineContext(topic_slug="Event Driven Architecture", run_id="run-pst-1")
    plan_res = plan_stage.execute(ctx, [])
    select_res = select_stage.execute(ctx, [plan_res])
    acq_res = acq_stage.execute(ctx, [plan_res, select_res])
    val_res = val_stage.execute(ctx, [plan_res, select_res, acq_res])
    fusion_res = fusion_stage.execute(ctx, [plan_res, select_res, acq_res, val_res])
    explain_res = explain_stage.execute(ctx, [plan_res, select_res, acq_res, val_res, fusion_res])
    persist_res = persist_stage.execute(ctx, [plan_res, select_res, acq_res, val_res, fusion_res, explain_res])

    assert persist_res.status == StageStatus.SUCCESS
    assert persist_res.stage_name == "research_persist"
    assert persist_res.output_data["persisted"] is True

    json_path = tmp_path / ".build" / "research" / "event_driven_architecture.json"
    md_path = tmp_path / ".build" / "research" / "event_driven_architecture.md"
    assert json_path.exists()
    assert md_path.exists()

    # Regression check: Verify top-level canonical ResearchReport schema fields in persisted JSON
    import json
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "discussions" in data
    assert "competitors" in data
    assert "risks" in data
    assert "target_audience" in data
    assert "fused_signals" not in data  # Strictly canonical schema - no redundant dual schema
    assert isinstance(data["discussions"], list)
    assert isinstance(data["competitors"], list)
    assert isinstance(data["risks"], list)
    assert isinstance(data["target_audience"], list)

    # Verify DecisionEngine reads top-level fields from persisted JSON without falling back to 100 defaults
    from ape.intelligence.decision.engine import DecisionEngine
    engine = DecisionEngine(tmp_path)
    report = engine.run_decision("Event Driven Architecture", "event_driven_architecture")

    # Dynamic calculation verification: When risks and competitors are present in canonical top-level schema,
    # raw feasibility and raw competition must be calculated from them (not defaulting to 100)
    expected_raw_feasibility = max(0, 100 - (len(data["risks"]) * 15))
    expected_raw_competition = max(0, 100 - (len(data["competitors"]) * 20))

    assert report.vector_scores["feasibility"] == expected_raw_feasibility
    assert report.vector_scores["competition"] == expected_raw_competition

    if len(data["risks"]) > 0:
        assert report.vector_scores["feasibility"] < 100
    if len(data["competitors"]) > 0:
        assert report.vector_scores["competition"] < 100


def test_research_persist_stage_long_topic_persistence(tmp_path):
    persist_stage = ResearchPersistStage(project_root=tmp_path)
    long_topic = "This is an extremely long topic designed specifically to trigger OS MAX_PATH limitations when converted into a slug and appended to a long file path inside the build directory structure"
    ctx = PipelineContext(topic_slug=long_topic, run_id="run-long-1")

    from ape.pipeline.contracts import StageResult
    fusion_res = StageResult(
        stage_name="evidence_fusion",
        status=StageStatus.SUCCESS,
        output_data={"fused_signals": {}, "overall_confidence": 0.85}
    )
    explain_res = StageResult(
        stage_name="explainability",
        status=StageStatus.SUCCESS,
        output_data={"summary": "Mock summary"},
        evidence={"stage_hash": "mock_hash"}
    )

    res = persist_stage.execute(ctx, [fusion_res, explain_res])
    assert res.status == StageStatus.SUCCESS

    # Verify the file was written without raising OS errors
    import os
    assert os.path.exists(res.output_data["json_path"])
    assert len(res.output_data["slug"]) <= 59
