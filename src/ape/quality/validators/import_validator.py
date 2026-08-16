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

        # Build the path entries to inject: project_root + src_root (if any).
        # src_root is provided by ValidationContext when a src/-layout package is detected.
        # If not provided, auto-detect by checking project_root/src/.
        paths_to_inject: list[str] = []

        str_root = str(context.project_root)
        if str_root not in sys.path:
            paths_to_inject.append(str_root)

        # src_root: explicit or auto-detected
        src_root = context.src_root
        if src_root is None:
            candidate = context.project_root / "src"
            if candidate.is_dir():
                src_root = candidate

        if src_root is not None:
            str_src = str(src_root)
            if str_src not in sys.path:
                paths_to_inject.append(str_src)

        for p in paths_to_inject:
            sys.path.insert(0, p)

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
            for p in paths_to_inject:
                if p in sys.path:
                    sys.path.remove(p)

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
