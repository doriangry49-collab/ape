from typer.testing import CliRunner
from ape.cli import app
from ape.intelligence.report import MarketReportFormatter
from ape.project import Project

runner = CliRunner()


def test_market_report_formatter_generates_artifacts(tmp_path, monkeypatch):
    """Verifies that MarketReportFormatter compiles research/decision data and saves artifacts."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)

    project = Project.load(tmp_path)
    formatter = MarketReportFormatter(project, offline=True)
    
    data = formatter.generate_report("home_local_services")

    assert data["metadata"]["topic"] == "home_local_services"
    assert "decision" in data["executive_summary"]
    assert "evidence_hash" in data["evidence_lineage"]

    # Verify build artifacts created
    json_path = tmp_path / ".build" / "reports" / "home_local_services-market-brief.json"
    md_path = tmp_path / ".build" / "reports" / "home_local_services-market-brief.md"

    assert json_path.exists()
    assert md_path.exists()

    md_text = md_path.read_text(encoding="utf-8")
    assert "APE Executive Market Brief" in md_text
    assert "Customer Pain Points" in md_text
    assert "Audit Evidence & Lineage" in md_text


def test_cli_report_command_execution(tmp_path, monkeypatch):
    """Verifies that ape report CLI command executes cleanly and outputs summary."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)

    # Initialize workspace
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["report", "home_local_services", "--offline"])
    assert result.exit_code == 0
    assert "APE Executive Market Brief Summary" in result.output
    assert "Policy Decision" in result.output
    assert "Status           : SUCCESS" in result.output
