"""
Unit Tests for Quality OS PR-Q2 Executable Validation Engine.
Tests SubprocessRunner, TimeoutManager, PytestValidator, SmokeValidator, and QualityRunner.
"""

from pathlib import Path

from ape.quality.contracts import ValidationContext, ValidationStatus
from ape.quality.runner import QualityRunner, SubprocessRunner, TimeoutManager
from ape.quality.validators.pytest_validator import PytestValidator
from ape.quality.validators.smoke_validator import SmokeValidator


def test_timeout_manager():
    tm = TimeoutManager({"custom": 42.0})
    assert tm.get_timeout("pytest") == 30.0
    assert tm.get_timeout("smoke") == 15.0
    assert tm.get_timeout("custom") == 42.0
    assert tm.get_timeout("nonexistent") == 15.0


def test_subprocess_runner_success(tmp_path: Path):
    runner = SubprocessRunner()
    res = runner.run(
        ["python", "-c", "print('hello world')"],
        cwd=tmp_path,
        validator_name="test_val",
        log_filename="test.log",
    )
    assert res.returncode == 0
    assert "hello world" in res.stdout
    assert res.log_path is not None
    assert res.log_path.exists()
    content = res.log_path.read_text(encoding="utf-8")
    assert "hello world" in content


def test_subprocess_runner_timeout(tmp_path: Path):
    tm = TimeoutManager({"quick": 0.2})
    runner = SubprocessRunner(timeout_manager=tm)
    res = runner.run(
        ["python", "-c", "import time; time.sleep(2)"],
        cwd=tmp_path,
        validator_name="quick",
        log_filename="timeout.log",
    )
    assert res.timed_out is True
    assert res.returncode == -1
    assert "timed out" in res.stderr


def test_pytest_validator_pass(tmp_path: Path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text("def test_ok(): assert True\n", encoding="utf-8")

    ctx = ValidationContext(
        project_root=tmp_path,
        topic_slug="test_topic",
        deliverables=["test_sample.py"],
        dry_run=False,
    )

    validator = PytestValidator()
    res = validator.validate(ctx)

    assert res.status == ValidationStatus.PASS
    assert res.score == 100.0
    assert "pytest.log" in res.logs
    assert len(res.artifacts) > 0


def test_pytest_validator_fail(tmp_path: Path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text("def test_bad(): assert False\n", encoding="utf-8")

    ctx = ValidationContext(
        project_root=tmp_path,
        topic_slug="test_topic",
        deliverables=["test_sample.py"],
        dry_run=False,
    )

    validator = PytestValidator()
    res = validator.validate(ctx)

    assert res.status == ValidationStatus.FAIL
    assert res.score == 0.0
    assert len(res.errors) > 0
    assert "pytest.log" in res.logs


def test_smoke_validator_pass(tmp_path: Path):
    main_file = tmp_path / "app.py"
    main_file.write_text(
        "def main():\n"
        "    return {'status': 'ok', 'message': 'running'}\n",
        encoding="utf-8",
    )

    ctx = ValidationContext(
        project_root=tmp_path,
        topic_slug="test_topic",
        deliverables=["app.py"],
        dry_run=False,
    )

    validator = SmokeValidator()
    res = validator.validate(ctx)

    assert res.status == ValidationStatus.PASS
    assert res.score == 100.0
    assert "smoke.log" in res.logs
    assert len(res.artifacts) > 0


def test_smoke_validator_fail(tmp_path: Path):
    main_file = tmp_path / "app.py"
    main_file.write_text(
        "def main():\n"
        "    raise ValueError('Smoke test fatal failure')\n",
        encoding="utf-8",
    )

    ctx = ValidationContext(
        project_root=tmp_path,
        topic_slug="test_topic",
        deliverables=["app.py"],
        dry_run=False,
    )

    validator = SmokeValidator()
    res = validator.validate(ctx)

    assert res.status == ValidationStatus.FAIL
    assert res.score == 0.0
    assert len(res.errors) > 0
    assert "smoke.log" in res.logs


def test_quality_runner(tmp_path: Path):
    main_file = tmp_path / "main.py"
    main_file.write_text("def main(): return {'status': 'ok'}\n", encoding="utf-8")

    test_file = tmp_path / "test_main.py"
    test_file.write_text("def test_pass(): assert True\n", encoding="utf-8")

    ctx = ValidationContext(
        project_root=tmp_path,
        topic_slug="test_topic",
        deliverables=["main.py", "test_main.py"],
        dry_run=False,
    )

    runner = QualityRunner()
    report = runner.run(ctx)

    assert report.quality_audit_passed is True
    assert report.overall_score == 100.0
    assert len(report.results) >= 4  # syntax, import, pytest, smoke
