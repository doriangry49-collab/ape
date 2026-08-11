"""
Quality OS Execution Infrastructure & Subsystem Runner — RFC-022 / PR-Q2 Specification.
Provides SubprocessRunner, TimeoutManager, and QualityRunner orchestrator.
"""

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from ape.quality.contracts import (
    QualityReport,
    ValidationContext,
    ValidationResult,
    ValidationStatus,
)


class TimeoutManager:
    """Configurable timeout manager for Quality OS validator executions."""

    DEFAULT_TIMEOUTS: dict[str, float] = {
        "pytest": 30.0,
        "smoke": 15.0,
        "syntax": 5.0,
        "import": 5.0,
        "default": 15.0,
    }

    def __init__(self, custom_timeouts: Optional[dict[str, float]] = None):
        self.timeouts = dict(self.DEFAULT_TIMEOUTS)
        if custom_timeouts:
            self.timeouts.update(custom_timeouts)

    def get_timeout(self, validator_name: str) -> float:
        """Get execution timeout in seconds for a specific validator."""
        return self.timeouts.get(validator_name.lower(), self.timeouts.get("default", 15.0))


@dataclass
class SubprocessResult:
    """Outcome of a SubprocessRunner execution."""
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    log_path: Optional[Path] = None


class SubprocessRunner:
    """Subprocess execution wrapper with timeout, output capture, and log dumping."""

    def __init__(self, timeout_manager: Optional[TimeoutManager] = None):
        self.timeout_manager = timeout_manager or TimeoutManager()

    def run(
        self,
        command: list[str],
        cwd: Path,
        validator_name: str = "default",
        log_filename: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        max_retries: int = 1,
        retry_delay_sec: float = 0.5,
    ) -> SubprocessResult:
        """Execute a subprocess command with timeout, retry on transient failure, and output capture."""
        timeout_sec = self.timeout_manager.get_timeout(validator_name)
        start_time = time.perf_counter()

        proc_env = os.environ.copy()
        pythonpath = str(cwd)
        if "PYTHONPATH" in proc_env and proc_env["PYTHONPATH"]:
            pythonpath = f"{str(cwd)}{os.pathsep}{proc_env['PYTHONPATH']}"
        proc_env["PYTHONPATH"] = pythonpath

        if env:
            proc_env.update(env)

        attempts = 0
        completed_res = None
        timed_out = False
        returncode = -1
        stdout = ""
        stderr = ""

        while attempts <= max_retries:
            attempts += 1
            timed_out = False
            try:
                completed = subprocess.run(
                    command,
                    cwd=str(cwd),
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    env=proc_env,
                )
                returncode = completed.returncode
                stdout = completed.stdout or ""
                stderr = completed.stderr or ""
                if returncode == 0 or timed_out:
                    break
                # If non-zero and retries remaining, wait briefly before retrying
                if attempts <= max_retries:
                    time.sleep(retry_delay_sec)
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                returncode = -1
                stdout = (exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout) or ""
                stderr = f"Execution timed out after {timeout_sec}s"
                break
            except Exception as exc:
                returncode = -1
                stdout = ""
                stderr = f"Subprocess launch failed: {exc}"
                break

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Log physical output if log_filename requested
        log_path: Optional[Path] = None
        if log_filename:
            log_dir = cwd / ".build" / "quality" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / log_filename
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"=== Quality OS Log: {validator_name} ===\n")
                f.write(f"Command : {' '.join(command)}\n")
                f.write(f"CWD     : {cwd}\n")
                f.write(f"Return  : {returncode} (TimedOut: {timed_out}, Attempts: {attempts})\n")
                f.write(f"Duration: {duration_ms:.2f} ms\n")
                f.write("--- STDOUT ---\n")
                f.write(stdout)
                f.write("\n--- STDERR ---\n")
                f.write(stderr)
                f.write("\n")

        return SubprocessResult(
            command=command,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
            log_path=log_path,
        )


class QualityRunner:
    """High-level Quality OS orchestrator that executes registered validators and produces QualityReport."""

    def __init__(self, registry: Optional[Any] = None):
        if registry is None:
            from ape.quality.registry import get_default_registry
            registry = get_default_registry()
        self.registry = registry

    def run(self, context: ValidationContext) -> QualityReport:
        """Run registered validators allowed by context.quality_profile and compute QualityReport."""
        from ape.quality.profiles import (
            get_profile_validators,
            get_validator_weight,
            normalize_validator_name,
        )

        profile_str = getattr(context, "quality_profile", "strict") or "strict"
        allowed_validator_names = get_profile_validators(profile_str)

        all_validators = self.registry.get_validators()
        validators = [v for v in all_validators if normalize_validator_name(getattr(v, "name", "")) in allowed_validator_names]

        results: list[ValidationResult] = []
        score_weights: dict[str, float] = {}

        for validator in validators:
            v_name = getattr(validator, "name", "unknown")
            score_weights[v_name] = get_validator_weight(v_name)
            try:
                res = validator.validate(context)
                results.append(res)
            except Exception as exc:
                # Catch validator crash gracefully
                results.append(
                    ValidationResult(
                        validator_name=v_name,
                        status=ValidationStatus.FAIL,
                        score=0.0,
                        duration_ms=0.0,
                        is_critical=getattr(validator, "is_critical", True),
                        weight=getattr(validator, "weight", 1.0),
                        errors=[f"Validator threw unhandled exception: {exc}"],
                    )
                )

        # Calculate overall weighted score and critical audit flag
        total_weight = sum(r.weight for r in results) if results else 1.0
        weighted_score = (
            sum(r.score * r.weight for r in results) / total_weight if results else 0.0
        )

        critical_passed = all(
            r.status in (ValidationStatus.PASS, ValidationStatus.WARN, ValidationStatus.SKIP)
            for r in results
            if r.is_critical
        )

        # Calculate Capability Breakdown
        capabilities = {
            "correctness": [r for r in results if normalize_validator_name(r.validator_name) in ("syntax", "import", "dependency")],
            "executability": [r for r in results if normalize_validator_name(r.validator_name) in ("smoke", "pytest", "runtime")],
            "packaging": [r for r in results if normalize_validator_name(r.validator_name) == "packaging"],
            "security": [r for r in results if normalize_validator_name(r.validator_name) == "security"],
        }
        capability_coverage = {}
        for cap_name, cap_results in capabilities.items():
            if cap_results:
                avg_cap_score = sum(r.score for r in cap_results) / len(cap_results)
                cap_passed = all(r.status in (ValidationStatus.PASS, ValidationStatus.WARN, ValidationStatus.SKIP) for r in cap_results)
                capability_coverage[cap_name] = {
                    "score": round(avg_cap_score, 2),
                    "passed": cap_passed,
                    "validators": [r.validator_name for r in cap_results],
                }

        # Calculate Release Confidence & Risk Level
        critical_count = sum(1 for r in results if r.is_critical)
        critical_pass_count = sum(1 for r in results if r.is_critical and r.status in (ValidationStatus.PASS, ValidationStatus.WARN, ValidationStatus.SKIP))
        critical_ratio = (critical_pass_count / critical_count) if critical_count else 1.0

        release_confidence = (weighted_score * 0.7) + (critical_ratio * 30.0)
        if not critical_passed or weighted_score < 60.0:
            risk_level = "CRITICAL" if any(r.status == ValidationStatus.FAIL and r.is_critical for r in results) else "HIGH"
        elif release_confidence < 85.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Generate Explainable Confidence Reasons
        confidence_reasons: list[str] = []
        for r in results:
            prefix = "+" if r.status in (ValidationStatus.PASS, ValidationStatus.SKIP) else "-"
            reason_text = f"{prefix} {r.validator_name.capitalize()} {r.status.value.upper()}"
            if r.status == ValidationStatus.WARN and r.warnings:
                reason_text += f": {r.warnings[0]}"
            elif r.status == ValidationStatus.FAIL and r.errors:
                reason_text += f": {r.errors[0]}"
            confidence_reasons.append(reason_text)

        summary = {
            "total_validators": len(results),
            "passed": sum(1 for r in results if r.status == ValidationStatus.PASS),
            "warned": sum(1 for r in results if r.status == ValidationStatus.WARN),
            "failed": sum(1 for r in results if r.status == ValidationStatus.FAIL),
            "skipped": sum(1 for r in results if r.status == ValidationStatus.SKIP),
            "critical_passed": critical_passed,
            "risk_level": risk_level,
            "quality_profile": profile_str,
        }

        report = QualityReport(
            overall_score=round(weighted_score, 2),
            quality_audit_passed=critical_passed,
            results=results,
            summary=summary,
            release_confidence=round(release_confidence, 2),
            risk_level=risk_level,
            capability_coverage=capability_coverage,
            confidence_reasons=confidence_reasons,
            quality_profile=profile_str,
            score_weights=score_weights,
        )

        # PR-Q3: Collect physical report artifacts and compute Merkle evidence lineage
        try:
            from ape.quality.evidence import QualityEvidenceBinder
            from ape.quality.reporter import QualityReportCollector

            collector = QualityReportCollector(context.project_root)
            saved_paths = collector.save_report(
                report,
                topic_slug=context.topic_slug,
                validator_names=[getattr(v, "name", str(v)) for v in validators],
            )
            report.reports = {k: str(v) for k, v in saved_paths.items()}

            binder = QualityEvidenceBinder(context.project_root)
            report.evidence_manifest = binder.build_evidence_manifest()
        except Exception:
            pass

        return report
