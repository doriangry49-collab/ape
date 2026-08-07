"""
Dependency Executable Validator — Capability Milestone C.
Parses declared dependencies in requirements.txt or pyproject.toml and cross-references them against imported modules.
"""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Set

from ape.quality.contracts import ValidationContext, ValidationResult, ValidationStatus
from ape.quality.runner import SubprocessRunner


# Standard library module names in Python 3
STD_LIB = sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else {
    "sys", "os", "math", "json", "time", "pathlib", "re", "dataclasses", "typing",
    "collections", "functools", "itertools", "logging", "hashlib", "subprocess",
    "shutil", "tempfile", "unittest", "ast", "enum", "io", "copy", "random"
}


class DependencyValidator:
    """Validator that verifies declared dependencies and detects undeclared imports."""

    def __init__(self, runner: Optional[SubprocessRunner] = None):
        self.runner = runner or SubprocessRunner()

    @property
    def name(self) -> str:
        return "dependency"

    @property
    def is_critical(self) -> bool:
        return False

    @property
    def weight(self) -> float:
        return 1.5

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate dependency files and imports across deliverables."""
        start_time = time.perf_counter()

        if context.dry_run:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=0.0,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["Dry run mode: skipped dependency validation"],
            )

        # 1. Discover declared dependencies
        declared_deps: Set[str] = set()
        dep_files: List[str] = []

        req_file = context.project_root / "requirements.txt"
        if req_file.exists():
            dep_files.append("requirements.txt")
            for line in req_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip().lower()
                    if pkg:
                        declared_deps.add(pkg)

        pyproject_file = context.project_root / "pyproject.toml"
        if pyproject_file.exists():
            dep_files.append("pyproject.toml")
            content = pyproject_file.read_text(encoding="utf-8")
            if "dependencies =" in content:
                # Basic string extraction for simple pyproject files
                for line in content.splitlines():
                    if '"' in line or "'" in line:
                        clean = line.replace('"', '').replace("'", '').replace(',', '').strip()
                        if clean and not clean.startswith("[") and not clean.startswith("#"):
                            pkg = clean.split("==")[0].split(">=")[0].strip().lower()
                            if pkg:
                                declared_deps.add(pkg)

        # 2. Extract third-party imports from Python deliverables
        imported_modules: Set[str] = set()
        python_files: List[Path] = []

        for item in context.deliverables:
            p = context.project_root / item
            if p.exists() and p.name.endswith(".py"):
                python_files.append(p)

        if not python_files:
            for p in context.project_root.glob("*.py"):
                if p.is_file():
                    python_files.append(p)

        for py_file in python_files:
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_mod = alias.name.split(".")[0]
                            if root_mod not in STD_LIB:
                                imported_modules.add(root_mod.lower())
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            root_mod = node.module.split(".")[0]
                            if root_mod not in STD_LIB:
                                imported_modules.add(root_mod.lower())
            except Exception:
                pass

        # Remove internal deliverable module names from imported_modules
        internal_mods = {p.stem.lower() for p in python_files}
        external_imports = imported_modules - internal_mods

        # Cross reference undeclared imports
        undeclared = []
        for imp in external_imports:
            # Check direct or normalized match
            if imp not in declared_deps and imp.replace("_", "-") not in declared_deps:
                undeclared.append(imp)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        log_dir = context.project_root / ".build" / "quality" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "dependency.log"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Quality OS Log: dependency ===\n")
            f.write(f"Declared Files   : {dep_files}\n")
            f.write(f"Declared Packages: {sorted(list(declared_deps))}\n")
            f.write(f"External Imports : {sorted(list(external_imports))}\n")
            f.write(f"Undeclared       : {undeclared}\n")

        logs = {"dependency.log": str(log_path)}
        metrics = {
            "declared_count": len(declared_deps),
            "external_import_count": len(external_imports),
            "undeclared_count": len(undeclared),
            "dep_files": dep_files,
        }

        if undeclared and not dep_files:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.WARN,
                score=70.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                warnings=[f"External imports detected {undeclared} but no dependency manifest (requirements.txt / pyproject.toml) found"],
                logs=logs,
                metrics=metrics,
            )

        if undeclared:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.WARN,
                score=80.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                warnings=[f"Undeclared third-party imports detected: {undeclared}"],
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
            findings=["Dependency validation passed: all external imports are declared"],
            logs=logs,
            metrics=metrics,
        )
