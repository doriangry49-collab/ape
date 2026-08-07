"""
SyntaxValidator — AST & Syntax correctness validator.
Parses Python deliverables via ast.parse() and JSON files via json.loads().
"""

import ast
import json
import time
from pathlib import Path

from ape.quality.contracts import (
    ValidationContext,
    ValidationResult,
    ValidationStatus,
)


class SyntaxValidator:
    """Validates syntax correctness of generated Python and JSON deliverable files."""

    @property
    def name(self) -> str:
        return "SyntaxValidator"

    @property
    def is_critical(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        return 2.0

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.perf_counter()
        findings: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []
        artifacts: list[str] = []

        target_files: list[Path] = []
        for d in context.deliverables:
            if d and isinstance(d, str):
                p = Path(d) if Path(d).is_absolute() else (context.project_root / d)
                if p.exists() and p.is_file():
                    target_files.append(p)

        if not target_files:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIP,
                score=100.0,
                duration_ms=duration_ms,
                findings=["No physical files found to perform syntax validation"],
            )

        passed_files = 0
        total_files = len(target_files)

        for p in target_files:
            artifacts.append(str(p))
            if p.suffix == ".py":
                try:
                    code = p.read_text(encoding="utf-8")
                    ast.parse(code, filename=str(p))
                    findings.append(f"Python AST parse PASSED: {p.name}")
                    passed_files += 1
                except SyntaxError as exc:
                    err_msg = f"SyntaxError in {p.name} (line {exc.lineno}): {exc.msg}"
                    errors.append(err_msg)
                except Exception as exc:
                    errors.append(f"Failed to read/parse {p.name}: {str(exc)}")
            elif p.suffix == ".json":
                try:
                    content = p.read_text(encoding="utf-8")
                    json.loads(content)
                    findings.append(f"JSON syntax PASSED: {p.name}")
                    passed_files += 1
                except json.JSONDecodeError as exc:
                    errors.append(f"JSONDecodeError in {p.name}: {str(exc)}")
            else:
                findings.append(f"Skipped non-code deliverable syntax check: {p.name}")
                passed_files += 1

        duration_ms = (time.perf_counter() - start_time) * 1000
        score = (passed_files / total_files * 100.0) if total_files > 0 else 100.0
        status = ValidationStatus.PASS if not errors else ValidationStatus.FAIL

        return ValidationResult(
            validator_name=self.name,
            status=status,
            score=score,
            duration_ms=duration_ms,
            findings=findings,
            warnings=warnings,
            errors=errors,
            artifacts=artifacts,
        )
