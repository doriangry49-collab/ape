"""
Packaging Executable Validator — Capability Milestone C.
Validates deliverable packaging structure, entrypoint definitions, and containment safety invariants.
"""

from __future__ import annotations

import time
from typing import List

from ape.quality.contracts import ValidationContext, ValidationResult, ValidationStatus


class PackagingValidator:
    """Validator that verifies project packaging structure and deliverable containment safety."""

    @property
    def name(self) -> str:
        return "packaging"

    @property
    def is_critical(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        return 1.5

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate packaging structure, entrypoint readiness, and containment invariants."""
        start_time = time.perf_counter()

        if context.dry_run:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=0.0,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["Dry run mode: skipped packaging validation"],
            )

        findings: List[str] = []
        warnings: List[str] = []
        errors: List[str] = []

        # 1. Path Containment Verification
        escaped_paths: List[str] = []
        for item in context.deliverables:
            try:
                target_path = (context.project_root / item).resolve()
                root_path = context.project_root.resolve()
                if not str(target_path).startswith(str(root_path)):
                    escaped_paths.append(item)
            except Exception:
                escaped_paths.append(item)

        if escaped_paths:
            errors.append(f"Containment violation: deliverables escape project root: {escaped_paths}")

        # 2. Packaging Manifest & Entrypoint Check
        has_pyproject = (context.project_root / "pyproject.toml").exists()
        has_requirements = (context.project_root / "requirements.txt").exists()
        has_entrypoint = any(
            (context.project_root / name).exists()
            for name in ("main.py", "app.py", "cli.py", "__main__.py")
        )

        if not has_entrypoint and context.deliverables:
            # Check if any deliverable is a python file
            has_entrypoint = any(d.endswith(".py") for d in context.deliverables)

        if has_pyproject:
            findings.append("Found valid pyproject.toml packaging manifest")
        elif has_requirements:
            findings.append("Found requirements.txt packaging manifest")
        else:
            warnings.append("No explicit packaging manifest (pyproject.toml / requirements.txt) found")

        if not has_entrypoint:
            warnings.append("No standard application entrypoint (main.py, app.py, cli.py) detected")
        else:
            findings.append("Verified application entrypoint structure")

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        log_dir = context.project_root / ".build" / "quality" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "packaging.log"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Quality OS Log: packaging ===\n")
            f.write(f"Pyproject Exists : {has_pyproject}\n")
            f.write(f"Reqs Exists      : {has_requirements}\n")
            f.write(f"Entrypoint Found : {has_entrypoint}\n")
            f.write(f"Escaped Paths    : {escaped_paths}\n")
            f.write(f"Errors           : {errors}\n")
            f.write(f"Warnings         : {warnings}\n")

        logs = {"packaging.log": str(log_path)}
        metrics = {
            "has_pyproject": has_pyproject,
            "has_requirements": has_requirements,
            "has_entrypoint": has_entrypoint,
            "escaped_count": len(escaped_paths),
        }

        if errors:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                score=0.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                errors=errors,
                warnings=warnings,
                logs=logs,
                metrics=metrics,
            )

        if warnings and not (has_pyproject or has_requirements or has_entrypoint):
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.WARN,
                score=75.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=findings,
                warnings=warnings,
                logs=logs,
                metrics=metrics,
            )

        return ValidationResult(
            validator_name=self.name,
            status=ValidationStatus.PASS,
            score=100.0,
            duration_ms=duration_ms,
            is_critical=self.is_critical,
            weight=self.weight,
            findings=findings,
            warnings=warnings,
            logs=logs,
            metrics=metrics,
        )
