"""
Unit tests for Capability Milestone F: Runtime Verification Engine & Explainable Release Confidence.
"""

from pathlib import Path
import pytest

from ape.quality.contracts import ValidationContext, ValidationStatus
from ape.quality.runner import QualityRunner
from ape.quality.validators.runtime_validator import RuntimeValidator


def test_runtime_validator_cli_script_pass(tmp_path: Path):
    """RuntimeValidator must execute clean CLI script and verify exit code 0."""
    script = tmp_path / "main.py"
    script.write_text("print('CLI execution clean')\n", encoding="utf-8")

    validator = RuntimeValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="cli_pass", deliverables=["main.py"])

    res = validator.validate(context)
    assert res.status == ValidationStatus.PASS
    assert res.metrics["runtime_error_count"] == 0
    assert (tmp_path / ".build" / "quality" / "logs" / "runtime.log").exists()


def test_runtime_validator_cli_script_fail(tmp_path: Path):
    """RuntimeValidator must fail CLI script that exits with non-zero code or error."""
    script = tmp_path / "main.py"
    script.write_text("raise ValueError('Runtime crash')\n", encoding="utf-8")

    validator = RuntimeValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="cli_fail", deliverables=["main.py"])

    res = validator.validate(context)
    assert res.status == ValidationStatus.FAIL
    assert res.metrics["runtime_error_count"] >= 1
    assert any("exit code" in err or "failed" in err for err in res.errors)


def test_runtime_validator_web_service_http_probe(tmp_path: Path):
    """RuntimeValidator must launch ephemeral web server, probe HTTP 200 OK, and terminate process."""
    web_script = tmp_path / "app.py"
    web_script.write_text("""import http.server
import os
import socketserver

port = int(os.environ.get("PORT", 8080))
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

httpd = socketserver.TCPServer(("127.0.0.1", port), Handler)
httpd.serve_forever()
""", encoding="utf-8")

    validator = RuntimeValidator()
    context = ValidationContext(project_root=tmp_path, topic_slug="web_pass", deliverables=["app.py"])

    res = validator.validate(context)
    assert res.status == ValidationStatus.PASS
    assert res.metrics["is_web_app"] is True
    assert any("HTTP" in f for f in res.findings)


def test_quality_runner_confidence_reasons_explainability(tmp_path: Path):
    """QualityRunner must populate explainable confidence_reasons in QualityReport."""
    (tmp_path / "main.py").write_text("print('App started')\n", encoding="utf-8")

    runner = QualityRunner()
    context = ValidationContext(project_root=tmp_path, topic_slug="explain_runner", deliverables=["main.py"])

    report = runner.run(context)
    assert len(report.confidence_reasons) > 0
    assert any("+ Syntax PASS" in r or "+ Runtime PASS" in r for r in report.confidence_reasons)
    report_dict = report.to_dict()
    assert "confidence_reasons" in report_dict
