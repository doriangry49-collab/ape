from typer.testing import CliRunner

from ape.cli import app

runner = CliRunner()


def test_research_report_structure() -> None:
    """Verifies that ResearchReport structure has all constitutional fields."""
    from datetime import UTC, datetime

    from ape.intelligence.research.models import ResearchReport

    report = ResearchReport(
        topic="Test Topic",
        target_audience=["devs"],
        competitors=["comp A"],
        pain_points=["expensive"],
        market_signals=["trending"],
        risks=["crowded"],
        confidence=0.85,
        sources=["HackerNews"],
        discussions=[{"title": "HN thread", "url": "http://hn.com"}],
        suggested_mvp=["Feature 1"],
        timestamp=datetime.now(UTC),
        next_recommended_action="VALIDATE",
        metadata={"schema_version": "1.0"},
    )

    assert report.topic == "Test Topic"
    assert "devs" in report.target_audience
    assert report.confidence == 0.85
    assert report.pain_points == ["expensive"]
    assert report.next_recommended_action == "VALIDATE"
    assert report.metadata["schema_version"] == "1.0"


def test_research_engine_offline_fallback(tmp_path) -> None:
    """Verifies that the research engine works offline and returns mock/fixture structures."""
    from ape.intelligence.research.engine import ResearchEngine
    from ape.project import Project

    project = Project.load(tmp_path)
    # Instantiate engine with offline mode or let it fallback automatically
    engine = ResearchEngine(project, offline=True)
    report = engine.run_research("AI Agents")

    assert report.topic == "AI Agents"
    assert len(report.pain_points) > 0
    assert len(report.market_signals) > 0
    assert report.confidence > 0.0
    assert "HackerNews" in report.sources


def test_research_reproducibility(tmp_path) -> None:
    """Verifies that identical inputs produce identical report structures."""
    from ape.intelligence.research.engine import ResearchEngine
    from ape.project import Project

    project = Project.load(tmp_path)
    engine = ResearchEngine(project, offline=True)

    report_1 = engine.run_research("AI Coding")
    report_2 = engine.run_research("AI Coding")

    assert report_1.topic == report_2.topic
    assert report_1.pain_points == report_2.pain_points
    assert report_1.market_signals == report_2.market_signals
    assert report_1.confidence == report_2.confidence


def test_cli_research_command_execution(tmp_path, monkeypatch) -> None:
    """Verifies that ape research command runs and creates JSON/Markdown artifacts."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)

    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["research", "AI tools"])
    assert result.exit_code == 0
    assert "Researching: 'AI tools'" in result.output

    # Check for artifacts in .build/research (canonical pointer - no timestamp)
    research_dir = tmp_path / ".build" / "research"
    assert research_dir.is_dir()
    assert (research_dir / "ai_tools.json").is_file()
    assert (research_dir / "ai_tools.md").is_file()

    # Check evidence log exists
    from ape.utils import get_artifact_history
    evidence = get_artifact_history(tmp_path / ".governance" / "evidence", "research")
    assert evidence.is_file()
