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


def test_research_engine_binds_matching_scan_lineage(tmp_path) -> None:
    """Verifies that ResearchEngine detects matching scan artifacts in .build/scans/ and attaches lineage."""
    from ape.intelligence.models import Opportunity, PainPoint
    from ape.intelligence.research.engine import ResearchEngine
    from ape.intelligence.scanner.persistence import ScanPersistence
    from ape.project import Project

    project = Project.load(tmp_path)
    persistence = ScanPersistence(tmp_path)

    opp = Opportunity(
        title="Home Local Services App",
        description="Local service booking platform",
        url="https://example.com/local",
        source="business_scanner",
        score=88,
        confidence=0.9,
        published_at="2026-07-31T12:00:00",  # type: ignore
        tags=["home_local_services"],
        pain_point=PainPoint(
            domain="local_services",
            description="High quote latency",
            frequency_signal=5,
            payment_signal=True,
            ai_solvable=True,
        ),
        is_hypothesis=True,
    )
    persistence.save_scan([opp], mode="business")

    engine = ResearchEngine(project, offline=True)
    report = engine.run_research("home_local_services")

    assert "discovery_lineage" in report.metadata
    lineage = report.metadata["discovery_lineage"]
    assert lineage["scan_mode"] == "business"
    assert lineage["opportunity_title"] == "Home Local Services App"
    assert lineage["opportunity_slug"] == "home_local_services_app"
    assert any("[Discovery Signal]" in p for p in report.pain_points)


def test_research_engine_handles_no_matching_scan_and_malformed_artifact(tmp_path) -> None:
    """Verifies that ResearchEngine handles missing scans and malformed JSON artifacts without crashing."""
    from ape.intelligence.research.engine import ResearchEngine
    from ape.project import Project

    project = Project.load(tmp_path)
    scans_dir = tmp_path / ".build" / "scans"
    scans_dir.mkdir(parents=True, exist_ok=True)
    (scans_dir / "2026-07-31-business-scan.json").write_text("CORRUPT_JSON{{{", encoding="utf-8")

    engine = ResearchEngine(project, offline=True)
    report = engine.run_research("unmatched_topic")

    assert report.topic == "unmatched_topic"
    assert "discovery_lineage" not in report.metadata
