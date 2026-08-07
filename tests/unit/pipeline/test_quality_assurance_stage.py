"""
Unit tests for QualityAssuranceStage.
"""

from dataclasses import dataclass
from pathlib import Path
import tempfile

from ape.pipeline.contracts import BasePipelineContext, StageStatus
from ape.pipeline.stages.quality_assurance import QualityAssuranceStage


@dataclass(frozen=True)
class DummyPipelineContext(BasePipelineContext):
    topic_slug: str = "test_topic"
    root: Path = Path.cwd()
    dry_run: bool = False


def test_quality_assurance_stage_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        py_file = root / "app.py"
        py_file.write_text("def run():\n    return True\n", encoding="utf-8")

        stage = QualityAssuranceStage()
        ctx = DummyPipelineContext(
            run_id="run_qa_1",
            topic_slug="test_app",
            root=root,
            metadata={"deliverables": ["app.py"]},
        )

        res = stage.execute(ctx)

        assert res.status == StageStatus.SUCCESS
        assert res.output_data["quality_audit_passed"] is True
        assert res.output_data["overall_score"] == 100.0


def test_quality_assurance_stage_failure_on_syntax_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        py_file = root / "bad_app.py"
        py_file.write_text("def broken(:\n", encoding="utf-8")

        stage = QualityAssuranceStage()
        ctx = DummyPipelineContext(
            run_id="run_qa_2",
            topic_slug="test_bad_app",
            root=root,
            metadata={"deliverables": ["bad_app.py"]},
        )

        res = stage.execute(ctx)

        assert res.status == StageStatus.FAILED
        assert res.output_data["quality_audit_passed"] is False
        assert res.output_data["overall_score"] < 80.0
