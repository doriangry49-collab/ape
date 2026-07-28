"""
RFC-010: CI Marker Tests — TDD RED Phase
Verify pytest 'integration' marker is registered and properly isolates
Docker integration tests from the unit test suite.
"""
import subprocess
import sys


def _pytest(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        capture_output=True,
        text=True,
    )


def test_integration_marker_is_registered():
    """pytest --markers must list the 'integration' marker."""
    result = _pytest("--markers")
    assert "integration" in result.stdout, (
        "Expected 'integration' marker to be registered in pyproject.toml "
        f"[tool.pytest.ini_options]. Got:\n{result.stdout}"
    )


def test_unit_run_excludes_integration_tests():
    """pytest -m 'not integration' must NOT collect test_docker_integration tests."""
    result = _pytest("-m", "not integration", "--collect-only", "-q")
    assert "test_docker_integration" not in result.stdout, (
        "test_docker_integration.py should be excluded when running "
        f"-m 'not integration'. Collected:\n{result.stdout}"
    )


def test_integration_run_collects_only_docker_tests():
    """pytest -m integration --collect-only must find TestDockerIntegration tests."""
    result = _pytest("-m", "integration", "--collect-only", "-q")
    assert "test_docker_integration" in result.stdout, (
        "Expected test_docker_integration.py to appear when running "
        f"-m integration. Got:\n{result.stdout}"
    )


def test_integration_marker_has_no_unknown_warning():
    """Running -m integration must not emit PytestUnknownMarkWarning."""
    result = _pytest("-m", "integration", "--collect-only", "-q")
    assert "PytestUnknownMarkWarning" not in result.stdout
    assert "PytestUnknownMarkWarning" not in result.stderr
