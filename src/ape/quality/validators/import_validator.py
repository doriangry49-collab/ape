"""
ImportValidator — Importability & Module loading validator.
Checks if generated Python modules can be safely loaded/imported.
"""

import importlib.util
import time
from pathlib import Path

from ape.quality.contracts import (
    ValidationContext,
    ValidationResult,
    ValidationStatus,
)


class ImportValidator:
    """Validates that Python deliverable files can be imported as Python modules."""

    @property
    def name(self) -> str:
        return "ImportValidator"

    @property
    def is_critical(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        return 1.5

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.perf_counter()
        findings: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []
        artifacts: list[str] = []

        py_files: list[Path] = []
        for d in context.deliverables:
            if d and isinstance(d, str):
                p = Path(d) if Path(d).is_absolute() else (context.project_root / d)
                if p.exists() and p.is_file() and p.suffix == ".py":
                    py_files.append(p)

        if not py_files:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIP,
                score=100.0,
                duration_ms=duration_ms,
                findings=["No Python files found for importability check"],
            )

        passed_files = 0
        total_files = len(py_files)

        import sys
        str_root = str(context.project_root)
        path_inserted = False
        if str_root not in sys.path:
            sys.path.insert(0, str_root)
            path_inserted = True

        try:
            for p in py_files:
                artifacts.append(str(p))
                module_name = f"_ape_val_{p.stem}"
                try:
                    spec = importlib.util.spec_from_file_location(module_name, p)
                    if spec is None or spec.loader is None:
                        errors.append(f"Could not load module spec for {p.name}")
                        continue
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    findings.append(f"Module import PASSED: {p.name}")
                    passed_files += 1
                except Exception as exc:
                    errors.append(f"ImportError in {p.name}: {type(exc).__name__}: {str(exc)}")
        finally:
            if path_inserted and str_root in sys.path:
                sys.path.remove(str_root)

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
