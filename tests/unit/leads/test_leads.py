import json
from pathlib import Path

import pytest

from ape.intelligence.leads.finder import LeadFinderEngine
from ape.intelligence.leads.models import LeadItem, LeadReport


def test_lead_item_and_report_schema(tmp_path: Path):
    lead = LeadItem(
        source_url="https://x.com/example_user/status/123456",
        source_type="twitter",
        quote="Test quote about database seeding",
        relevance_reason="Relevant discussion",
        suggested_approach="Suggested draft outreach",
        verification_status="VERIFIED_EXISTS",
    )
    data = lead.to_dict()
    assert data["source_type"] == "twitter"
    assert data["verification_status"] == "VERIFIED_EXISTS"

    report = LeadReport(
        product="test-product",
        pain_point="test-pain",
        discovered_at="2026-09-06T12:00:00Z",
        total_leads=1,
        verified_leads=1,
        leads=[lead],
    )
    report_dict = report.to_dict()
    assert report_dict["total_leads"] == 1
    assert len(report_dict["leads"]) == 1


def test_disambiguation_and_official_filtering(tmp_path: Path):
    engine = LeadFinderEngine(project_root=tmp_path)

    # Haskell Snap Framework should be filtered out
    assert engine._is_valid_db_context("How to use MonadState in Haskell Snaplet") is False
    assert engine._is_valid_db_context("Generate seed data using Snaplet for postgres") is True

    # Official company accounts should be filtered out
    assert engine._is_official_account("https://x.com/snaplet") is True
    assert engine._is_official_account("https://x.com/jianreis/status/1807707851340579155") is False


def test_lead_finder_v02_distinct_approaches(tmp_path: Path):
    engine = LeadFinderEngine(project_root=tmp_path)
    report = engine.find_leads(product="ai-db-seeder", pain_point="Snaplet shutdown, cross-column state logic")

    assert report.total_leads >= 4
    approaches = [lead.suggested_approach for lead in report.leads]

    # Verify all suggested approaches are unique and non-template
    assert len(set(approaches)) == len(approaches)
    assert len(approaches) >= 4

    # Verify no official accounts or Haskell framework links present
    for lead in report.leads:
        assert "x.com/snaplet$" not in lead.source_url
        assert "MonadState" not in lead.quote


def test_save_deliverable_writes_json(tmp_path: Path):
    engine = LeadFinderEngine(project_root=tmp_path)

    lead = LeadItem(
        source_url="https://x.com/example_user/status/123456",
        source_type="twitter",
        quote="Test quote about database seeding",
        relevance_reason="Relevant discussion",
        suggested_approach="Suggested draft outreach",
        verification_status="VERIFIED_EXISTS",
    )
    report = LeadReport(
        product="test-product",
        pain_point="test-pain",
        discovered_at="2026-09-06T12:00:00Z",
        total_leads=1,
        verified_leads=1,
        leads=[lead],
    )

    output_path = tmp_path / "deliverables" / "leads_test-product.json"
    result_path = engine.save_deliverable(report, output_path=output_path)

    assert result_path == output_path
    assert output_path.exists()

    with open(output_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data == report.to_dict()


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # Special characters: &, !, . stripped; surrounding spaces collapse into one underscore
        ("AI & DB Seeder v1.0!", "ai_db_seeder_v10"),
        # Multiple consecutive spaces collapse into a single underscore
        ("hello   world", "hello_world"),
        # Leading/trailing whitespace stripped, internal punctuation removed
        ("  spaced  out  ", "spaced_out"),
        # Hyphens and spaces both collapse into underscore
        ("test-case (v2.0)", "test_case_v20"),
        # Mixed punctuation and symbols
        ("C++ / Rust: Systems!!", "c_rust_systems"),
        # Empty-ish / whitespace only
        ("   ", ""),
        # Single word, no change beyond lowering
        ("Seeder", "seeder"),
        # Underscores in input are word chars, preserved, adjacent spaces still collapse
        ("foo _ bar", "foo___bar"),
    ],
)
def test_slugify_edge_cases(input_text: str, expected: str):
    engine = LeadFinderEngine(project_root=Path("/tmp"))
    assert engine._slugify(input_text) == expected


def test_is_official_account_trailing_slash(tmp_path: Path):
    """Regression: URLs with trailing slash must still match official-account patterns."""
    engine = LeadFinderEngine(project_root=tmp_path)
    # 1. Trailing slash was broken (regex ended with '$'); now fixed
    assert engine._is_official_account("https://x.com/snaplet/") is True
    # 2. Without trailing slash still works
    assert engine._is_official_account("https://x.com/snaplet") is True
    # 3. Empty string guarded
    assert engine._is_official_account("") is False
    # 4. None guarded
    assert engine._is_official_account(None) is False


def test_lead_item_from_dict_round_trip():
    lead = LeadItem(
        source_url="https://x.com/example_user/status/123456",
        source_type="twitter",
        quote="Test quote about database seeding",
        relevance_reason="Relevant discussion",
        suggested_approach="Suggested draft outreach",
        verification_status="VERIFIED_EXISTS",
    )
    data = lead.to_dict()
    restored = LeadItem.from_dict(data)
    assert restored.source_url == lead.source_url
    assert restored.source_type == lead.source_type
    assert restored.quote == lead.quote
    assert restored.relevance_reason == lead.relevance_reason
    assert restored.suggested_approach == lead.suggested_approach
    assert restored.verification_status == lead.verification_status


def test_lead_report_from_dict_round_trip():
    lead = LeadItem(
        source_url="https://x.com/example_user/status/123456",
        source_type="twitter",
        quote="Test quote about database seeding",
        relevance_reason="Relevant discussion",
        suggested_approach="Suggested draft outreach",
        verification_status="VERIFIED_EXISTS",
    )
    report = LeadReport(
        product="test-product",
        pain_point="test-pain",
        discovered_at="2026-09-06T12:00:00Z",
        total_leads=1,
        verified_leads=1,
        leads=[lead],
    )
    data = report.to_dict()
    restored = LeadReport.from_dict(data)
    assert restored.product == report.product
    assert restored.pain_point == report.pain_point
    assert restored.discovered_at == report.discovered_at
    assert restored.total_leads == report.total_leads
    assert restored.verified_leads == report.verified_leads
    assert len(restored.leads) == 1
    assert isinstance(restored.leads[0], LeadItem)
    assert restored.leads[0].source_url == lead.source_url


def test_load_deliverable_happy_path(tmp_path: Path):
    engine = LeadFinderEngine(project_root=tmp_path)
    lead = LeadItem(
        source_url="https://x.com/example_user/status/123456",
        source_type="twitter",
        quote="Test quote about database seeding",
        relevance_reason="Relevant discussion",
        suggested_approach="Suggested draft outreach",
        verification_status="VERIFIED_EXISTS",
    )
    report = LeadReport(
        product="test-product",
        pain_point="test-pain",
        discovered_at="2026-09-06T12:00:00Z",
        total_leads=1,
        verified_leads=1,
        leads=[lead],
    )
    json_path = tmp_path / "deliverables" / "leads_test-product.json"
    engine.save_deliverable(report, output_path=json_path)
    loaded = engine.load_deliverable(str(json_path))
    assert loaded.product == report.product
    assert loaded.pain_point == report.pain_point
    assert loaded.total_leads == report.total_leads
    assert len(loaded.leads) == 1
    assert loaded.leads[0].source_url == lead.source_url


def test_load_deliverable_file_not_found(tmp_path: Path):
    engine = LeadFinderEngine(project_root=tmp_path)
    with pytest.raises(ValueError, match="Deliverable file not found"):
        engine.load_deliverable(str(tmp_path / "nonexistent.json"))


def test_load_deliverable_invalid_json(tmp_path: Path):
    engine = LeadFinderEngine(project_root=tmp_path)
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        engine.load_deliverable(str(bad_json))
