"""
Unit tests for Capability Milestone D: Security & Boundary Containment Engine.
"""

from pathlib import Path

from ape.quality.contracts import ValidationContext, ValidationStatus
from ape.quality.runner import QualityRunner
from ape.quality.validators.security_validator import SecurityValidator


def test_security_validator_safe_code(tmp_path: Path):
    """SecurityValidator must pass clean code containing no unsafe calls or secrets."""
    safe_file = tmp_path / "safe_app.py"
    safe_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    validator = SecurityValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="safe", deliverables=["safe_app.py"])

    res = validator.validate(context)
    assert res.status == ValidationStatus.PASS
    assert res.metrics["security_error_count"] == 0
    assert (tmp_path / ".build" / "quality" / "logs" / "security.log").exists()


def test_security_validator_unsafe_eval_exec_pickle(tmp_path: Path):
    """SecurityValidator must fail code containing eval(), exec(), pickle.loads(), or subprocess shell=True."""
    unsafe_file = tmp_path / "unsafe_app.py"
    unsafe_file.write_text("""
import pickle
import subprocess

def run_user_input(code):
    eval(code)
    exec(code)
    pickle.loads(b"")
    subprocess.run("ls", shell=True)
""", encoding="utf-8")

    validator = SecurityValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="unsafe", deliverables=["unsafe_app.py"])

    res = validator.validate(context)
    assert res.status == ValidationStatus.FAIL
    assert res.metrics["security_error_count"] >= 4
    assert any("eval" in err for err in res.errors)
    assert any("exec" in err for err in res.errors)
    assert any("pickle" in err for err in res.errors)
    assert any("shell=True" in err for err in res.errors)


def test_security_validator_secret_scanning(tmp_path: Path):
    """SecurityValidator must detect hardcoded API keys and credentials."""
    secret_file = tmp_path / "config.py"
    secret_file.write_text("""
OPENAI_KEY = "sk-proj-1234567890abcdef1234567890abcdef12"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
""", encoding="utf-8")

    validator = SecurityValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="secret", deliverables=["config.py"])

    res = validator.validate(context)
    assert res.status == ValidationStatus.FAIL
    assert res.metrics["secret_finding_count"] >= 2
    assert any("exposed credential" in err for err in res.errors)


def test_quality_runner_security_capability_integration(tmp_path: Path):
    """QualityRunner must include security in capability_coverage breakdown."""
    (tmp_path / "main.py").write_text("print('clean app')\n", encoding="utf-8")

    runner = QualityRunner()
    context = ValidationContext(project_root=tmp_path, topic_slug="sec_runner", deliverables=["main.py"])

    report = runner.run(context)
    assert "security" in report.capability_coverage
    assert report.capability_coverage["security"]["passed"] is True
    assert "security" in report.capability_coverage["security"]["validators"]
