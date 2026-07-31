import json
from datetime import UTC, datetime
from pathlib import Path
from typer.testing import CliRunner

from ape.cli import app
from ape.intelligence.models import Opportunity, PainPoint
from ape.intelligence.scanner.persistence import ScanPersistenceService

runner = CliRunner()


def test_save_scan_creates_json_and_md_artifacts(tmp_path):
    service = ScanPersistenceService(tmp_path)
    opp = Opportunity(
        title="AI Agent CLI",
        description="CLI tool for devs",
        url="https://example.com/cli",
        source="github_trending",
        score=85,
        confidence=0.9,
        published_at=datetime.now(UTC),
        tags=["cli", "ai"],
    )

    json_path, md_path = service.save_scan([opp], mode="tech")

    assert json_path.exists()
    assert md_path.exists()
    assert json_path.name.endswith("-tech-scan.json")
    assert md_path.name.endswith("-tech-scan.md")

    content = json.loads(json_path.read_text(encoding="utf-8"))
    assert content["metadata"]["mode"] == "tech"
    assert content["metadata"]["total_opportunities"] == 1
    assert content["opportunities"][0]["title"] == "AI Agent CLI"
    assert content["opportunities"][0]["score"] == 85


def test_save_scan_handles_business_opportunities_with_pain_points(tmp_path):
    service = ScanPersistenceService(tmp_path)
    pain = PainPoint(
        domain="home_local_services",
        description="High manual dispatch overhead",
        frequency_signal=10,
        payment_signal=True,
        ai_solvable=True,
    )
    opp = Opportunity(
        title="Discovery in home_local_services",
        description="Automated scan for local services",
        url="ape://discovery/home_local_services",
        source="orchestrator",
        score=75,
        confidence=0.8,
        published_at=datetime.now(UTC),
        tags=["home_local_services"],
        pain_point=pain,
    )

    json_path, _ = service.save_scan([opp], mode="business")
    content = json.loads(json_path.read_text(encoding="utf-8"))

    assert content["metadata"]["mode"] == "business"
    assert content["opportunities"][0]["pain_point"]["domain"] == "home_local_services"
    assert content["opportunities"][0]["pain_point"]["description"] == "High manual dispatch overhead"


def test_list_scans_returns_sorted_paths(tmp_path):
    service = ScanPersistenceService(tmp_path)
    opp = Opportunity(
        title="Demo Topic",
        description="Demo",
        url="https://example.com",
        source="test",
        score=50,
        confidence=0.5,
        published_at=datetime.now(UTC),
        tags=[],
    )

    service.save_scan([opp], mode="tech")
    service.save_scan([opp], mode="business")

    scans = service.list_scans()
    assert len(scans) == 2
    assert any("tech-scan.json" in p.name for p in scans)
    assert any("business-scan.json" in p.name for p in scans)


def test_cli_scan_persists_scan_artifacts(tmp_path, monkeypatch):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".ape").mkdir()
    (workspace_dir / ".ape" / "config.toml").write_text(
        '[ape]\nname = "demo"\n', encoding="utf-8"
    )

    monkeypatch.chdir(workspace_dir)
    result = runner.invoke(app, ["scan", "--offline", "--mode", "business"])
    assert result.exit_code == 0
    assert "Saved scan artifacts to .build" in result.output

    scans_dir = workspace_dir / ".build" / "scans"
    assert scans_dir.exists()
    saved_files = list(scans_dir.glob("*-business-scan.json"))
    assert len(saved_files) >= 1
