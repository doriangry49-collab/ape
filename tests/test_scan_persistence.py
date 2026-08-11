import json
from datetime import UTC, datetime
from pathlib import Path

from ape.intelligence.models import BusinessEvidence, Opportunity, PainPoint
from ape.intelligence.scanner.persistence import ScanPersistence


def test_scan_persistence_saves_json_and_md(tmp_path: Path):
    project_root = tmp_path
    persistence = ScanPersistence(project_root)

    opp = Opportunity(
        title="Test Opportunity",
        description="A test opportunity for persistence.",
        url="https://example.com/test",
        source="test_source",
        score=85,
        confidence=0.9,
        published_at=datetime.now(UTC),
        tags=["test", "demo"],
        pain_point=PainPoint(
            domain="testing",
            description="Lacking automated tests.",
            frequency_signal=5,
            payment_signal=True,
            ai_solvable=True,
        ),
        business_evidence=[BusinessEvidence.all_unknown()],
        is_hypothesis=True,
    )

    json_path, md_path = persistence.save_scan([opp], mode="tech")

    assert json_path.exists()
    assert md_path.exists()
    assert ".build" in str(json_path)
    assert "scans" in str(json_path)

    json_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_data["metadata"]["mode"] == "tech"
    assert json_data["metadata"]["total_opportunities"] == 1

    first_opp = json_data["opportunities"][0]
    assert first_opp["title"] == "Test Opportunity"
    assert first_opp["slug"] == "test_opportunity"
    assert first_opp["score"] == 85
    assert first_opp["pain_point"]["domain"] == "testing"
    assert first_opp["business_evidence_count"] == 1


def test_scan_persistence_handles_empty_opportunities(tmp_path: Path):
    persistence = ScanPersistence(tmp_path)
    json_path, md_path = persistence.save_scan([], mode="business")

    assert json_path.exists()
    assert md_path.exists()

    json_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_data["metadata"]["total_opportunities"] == 0
    assert json_data["opportunities"] == []

    md_text = md_path.read_text(encoding="utf-8")
    assert "No opportunities found" in md_text


def test_scan_persistence_load_latest_scan(tmp_path: Path):
    persistence = ScanPersistence(tmp_path)
    opp = Opportunity(
        title="Latest Opp",
        description="Latest",
        url="http://latest",
        source="latest",
        score=90,
        confidence=0.8,
        published_at=datetime.now(UTC),
        tags=["latest"],
    )

    persistence.save_scan([opp], mode="business")
    latest = persistence.load_latest_scan(mode="business")

    assert latest is not None
    assert latest["metadata"]["mode"] == "business"
    assert latest["opportunities"][0]["title"] == "Latest Opp"
