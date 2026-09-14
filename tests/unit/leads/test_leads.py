from pathlib import Path
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
