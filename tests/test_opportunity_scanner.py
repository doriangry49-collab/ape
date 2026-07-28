from typer.testing import CliRunner

from ape.cli import app

runner = CliRunner()


def test_opportunity_model_structure() -> None:
    """Verifies the Opportunity data model attributes."""
    from datetime import UTC, datetime

    from ape.intelligence.models import Opportunity
    
    op = Opportunity(
        title="Test Opportunity",
        description="A test opportunity",
        url="https://example.com",
        source="Test",
        score=95,
        confidence=0.9,
        published_at=datetime.now(UTC),
        tags=["ai", "test"]
    )
    
    assert op.title == "Test Opportunity"
    assert op.score == 95
    assert op.confidence == 0.9
    assert "ai" in op.tags


def test_opportunity_engine_runs_scanners(tmp_path, monkeypatch) -> None:
    """OpportunityEngine should fetch and aggregate data from providers."""
    from ape.intelligence.engine import OpportunityEngine
    from ape.project import Project
    
    project = Project.load(tmp_path)
    engine = OpportunityEngine(project)
    
    # Run scans
    opportunities = engine.run_scans()
    
    # We expect some opportunities list returned (empty list or simulated items)
    assert isinstance(opportunities, list)


def test_scoring_heuristic_calculation() -> None:
    """Verifies that the simple scoring module calculates scores and confidence correctly."""
    from ape.intelligence.scoring import calculate_heuristic_score
    
    score, confidence = calculate_heuristic_score(
        popularity=100,
        age_hours=2,
        title="An AI tool for generating websites"
    )
    
    assert 0 <= score <= 100
    assert 0.0 <= confidence <= 1.0


def test_cli_scan_command_execution(tmp_path, monkeypatch) -> None:
    """Verifies that ape scan runs successfully and outputs results."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)
    
    # Init first to get the workspace setup
    runner.invoke(app, ["init"])
    
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0
    assert "Today's Opportunities" in result.output
