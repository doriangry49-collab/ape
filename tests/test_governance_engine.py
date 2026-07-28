import json

import pytest
from typer.testing import CliRunner

from ape.cli import app

runner = CliRunner()


def test_project_state_schema_validation(tmp_path, monkeypatch) -> None:
    """Verifies that project_state.json conforms to its schema constraints."""
    # This will test the validator functionality that checks the schema.
    # Since the schema and validation logic don't exist yet, this will fail.
    from ape.services.governance_validator import validate_project_state
    
    # Create invalid state data
    invalid_state = {
        "version": "not-a-number",
        "current_sprint": 7.0
    }
    
    state_file = tmp_path / "project_state.json"
    state_file.write_text(json.dumps(invalid_state), encoding="utf-8")
    
    with pytest.raises(ValueError):
        validate_project_state(state_file)


def test_ape_context_generates_files(tmp_path, monkeypatch) -> None:
    """ape context --all should generate markdown, json, xml, and START_HERE_AI.md."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)
    
    # Initialize workspace
    runner.invoke(app, ["init"])
    
    # Run context builder
    result = runner.invoke(app, ["context", "--all"])
    
    assert result.exit_code == 0
    assert (tmp_path / "START_HERE_AI.md").is_file()
    assert (tmp_path / ".build" / "context.md").is_file()
    assert (tmp_path / ".build" / "context.json").is_file()
    assert (tmp_path / ".build" / "context.xml").is_file()
    
    # Check semantic tags in context.xml
    xml_content = (tmp_path / ".build" / "context.xml").read_text(encoding="utf-8")
    expected_tags = [
        "<north_star>",
        "<constitution>",
        "<current_state>",
        "<decisions>",
        "<roadmap>",
        "<evidence>",
        "<open_tasks>",
    ]
    for tag in expected_tags:
        assert tag in xml_content


def test_ape_validate_runs_checks_and_creates_evidence(tmp_path, monkeypatch) -> None:
    """ape validate should execute check runs and output evidence.json."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)
    
    runner.invoke(app, ["init"])
    
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    
    evidence_path = tmp_path / ".build" / "evidence.json"
    assert evidence_path.is_file()
    
    evidence_data = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert "shipping_velocity" in evidence_data
    assert "tests" in evidence_data
    assert "governance" in evidence_data


def test_ape_doctor_governance_reporting(tmp_path, monkeypatch) -> None:
    """ape doctor --governance should return scoring diagnostics and output Rich tables."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PWD", raising=False)
    
    runner.invoke(app, ["init"])
    
    result = runner.invoke(app, ["doctor", "--governance"])
    assert result.exit_code == 0
    assert "Governance Health Status" in result.output
    assert "Overall Governance Score" in result.output
