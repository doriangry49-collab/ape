"""
Pytest Executable Validator — RFC-022 / PR-Q2 Specification.
Executes pytest against test deliverables using SubprocessRunner and captures physical log evidence.
"""

import sys
import time
from pathlib import Path
from typing import Optional

from ape.quality.contracts import ValidationContext, ValidationResult, ValidationStatus
from ape.quality.runner import SubprocessRunner


class PytestValidator:
    """Executable Validator that runs pytest against generated test suites."""

    def __init__(self, runner: Optional[SubprocessRunner] = None):
        self.runner = runner or SubprocessRunner()

    @property
    def name(self) -> str:
        return "pytest"

    @property
    def is_critical(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        return 2.0

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Execute pytest validation on deliverables or discovered test files."""
        start_time = time.perf_counter()

        if context.dry_run:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=0.0,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["Dry run mode: skipped pytest execution"],
            )

        # Discover test files
        test_files: list[Path] = []
        for item in context.deliverables:
            p = context.project_root / item
            if p.exists() and p.name.startswith("test_") and p.name.endswith(".py"):
                test_files.append(p)

        if not test_files:
            # Check for any test_*.py in root
            for p in context.project_root.glob("test_*.py"):
                if p.is_file():
                    test_files.append(p)

        if not test_files:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIP,
                score=100.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["No test files (test_*.py) found in deliverables or project root"],
            )

        target_test = test_files[0]
        junit_xml_path = context.project_root / ".build" / "quality" / "reports" / "junit.xml"
        junit_xml_path.parent.mkdir(parents=True, exist_ok=True)

        # Resolve src_root for PYTHONPATH injection (handles src/-layout packages)
        import os
        src_root = context.src_root
        if src_root is None:
            candidate = context.project_root / "src"
            if candidate.is_dir():
                src_root = candidate

        extra_env: dict[str, str] = {}
        if src_root is not None:
            existing = os.environ.get("PYTHONPATH", "")
            extra_env["PYTHONPATH"] = str(src_root) + (os.pathsep + existing if existing else "")

        # Use absolute path for test file to avoid "file not found" when cwd != project_root
        cmd = [sys.executable, "-m", "pytest", str(target_test.resolve()), "-q", "--tb=short", f"--junitxml={junit_xml_path}"]
        sub_res = self.runner.run(
            cmd,
            cwd=context.project_root,
            validator_name=self.name,
            log_filename="pytest.log",
            env=extra_env if extra_env else None,
        )

        artifacts = []
        logs = {}
        if sub_res.log_path:
            rel_log = str(sub_res.log_path.relative_to(context.project_root))
            artifacts.append(rel_log)
            logs["pytest.log"] = str(sub_res.log_path)

        junit_metrics = self._parse_junit_metrics(junit_xml_path)

        if sub_res.timed_out:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                score=0.0,
                duration_ms=sub_res.duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                errors=[f"Pytest execution timed out for {target_test.name}"],
                artifacts=artifacts,
                logs=logs,
                metrics={"exit_code": -1, "test_file": target_test.name, **junit_metrics},
            )

        if sub_res.returncode == 0:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=sub_res.duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=[f"Pytest suite passed cleanly: {target_test.name}"],
                artifacts=artifacts,
                logs=logs,
                metrics={"exit_code": 0, "test_file": target_test.name, **junit_metrics},
            )

        # Test failure
        stderr_summary = sub_res.stderr.strip() or sub_res.stdout.strip()
        lines = [line for line in stderr_summary.splitlines() if line.strip()]
        last_err = lines[-1] if lines else "pytest returned non-zero exit code"

        return ValidationResult(
            validator_name=self.name,
            status=ValidationStatus.FAIL,
            score=0.0,
            duration_ms=sub_res.duration_ms,
            is_critical=self.is_critical,
            weight=self.weight,
            errors=[f"Pytest failed for {target_test.name}: {last_err}"],
            artifacts=artifacts,
            logs=logs,
            metrics={"exit_code": sub_res.returncode, "test_file": target_test.name, **junit_metrics},
        )

    def _parse_junit_metrics(self, junit_path: Path) -> dict:
        """Helper to parse basic test metrics from generated JUnit XML file."""
        if not junit_path.exists():
            return {}
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(junit_path)
            root = tree.getroot()
            # Handle root being <testsuites> or <testsuite>
            suite = root if root.tag == "testsuite" else root.find("testsuite")
            if suite is not None:
                return {
                    "total_tests": int(suite.attrib.get("tests", 0)),
                    "failures": int(suite.attrib.get("failures", 0)),
                    "errors": int(suite.attrib.get("errors", 0)),
                    "skipped": int(suite.attrib.get("skipped", 0)),
                    "suite_time": float(suite.attrib.get("time", 0.0)),
                }
        except Exception:
            pass
        return {}
