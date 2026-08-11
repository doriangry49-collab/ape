"""
Smoke Executable Validator — RFC-022 / PR-Q2 Specification.
Executes generated entrypoints to verify live runtime smoke executability and captures physical log evidence.
"""

import sys
import time
from pathlib import Path
from typing import Optional

from ape.quality.contracts import ValidationContext, ValidationResult, ValidationStatus
from ape.quality.runner import SubprocessRunner


class SmokeValidator:
    """Executable Validator that executes deliverable entrypoints for smoke verification."""

    def __init__(self, runner: Optional[SubprocessRunner] = None):
        self.runner = runner or SubprocessRunner()

    @property
    def name(self) -> str:
        return "smoke"

    @property
    def is_critical(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        return 2.0

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Execute entrypoint smoke test against deliverables."""
        start_time = time.perf_counter()

        if context.dry_run:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=0.0,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["Dry run mode: skipped smoke test execution"],
            )

        # Discover entrypoint deliverable python files
        entrypoint: Optional[Path] = None
        for item in context.deliverables:
            p = context.project_root / item
            if p.exists() and p.name.endswith(".py") and not p.name.startswith("test_"):
                entrypoint = p
                break

        if not entrypoint:
            # Fallback search in project root
            for candidate in ["main.py", "important_file.py", "app.py"]:
                p = context.project_root / candidate
                if p.is_file():
                    entrypoint = p
                    break

        if not entrypoint:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIP,
                score=100.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["No runnable python entrypoint found in deliverables or project root"],
            )

        module_name = entrypoint.stem
        # Inline smoke execution snippet
        smoke_code = (
            f"import ast, {module_name}; "
            f"ast.parse(open('{entrypoint.name}').read()); "
            f"main_fn = getattr({module_name}, 'main', None); "
            f"res = main_fn() if callable(main_fn) else {{'status': 'ok', 'message': 'module imported cleanly'}}; "
            f"print('Smoke Output:', res)"
        )

        cmd = [sys.executable, "-c", smoke_code]
        sub_res = self.runner.run(
            cmd,
            cwd=context.project_root,
            validator_name=self.name,
            log_filename="smoke.log",
        )

        artifacts = []
        logs = {}
        if sub_res.log_path:
            rel_log = str(sub_res.log_path.relative_to(context.project_root))
            artifacts.append(rel_log)
            logs["smoke.log"] = str(sub_res.log_path)

        if sub_res.timed_out:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                score=0.0,
                duration_ms=sub_res.duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                errors=[f"Smoke execution timed out for {entrypoint.name}"],
                artifacts=artifacts,
                logs=logs,
            )

        if sub_res.returncode == 0:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=sub_res.duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=[f"Smoke test executed successfully for {entrypoint.name}"],
                artifacts=artifacts,
                logs=logs,
                metrics={"exit_code": 0, "entrypoint": entrypoint.name},
            )

        err_msg = sub_res.stderr.strip() or sub_res.stdout.strip()
        last_err = err_msg.splitlines()[-1] if err_msg else "Non-zero exit code"
        return ValidationResult(
            validator_name=self.name,
            status=ValidationStatus.FAIL,
            score=0.0,
            duration_ms=sub_res.duration_ms,
            is_critical=self.is_critical,
            weight=self.weight,
            errors=[f"Smoke test failed for {entrypoint.name}: {last_err}"],
            artifacts=artifacts,
            logs=logs,
            metrics={"exit_code": sub_res.returncode, "entrypoint": entrypoint.name},
        )
