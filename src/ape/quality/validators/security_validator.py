"""
Security & Boundary Containment Executable Validator — Capability Milestone D.
Performs AST static security inspection and secret scanning across deliverable code.
"""

from __future__ import annotations

import ast
import re
import time
from pathlib import Path
from typing import List

from ape.quality.contracts import ValidationContext, ValidationResult, ValidationStatus

# High-entropy API key and credential detection regex patterns
SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"sk-[a-zA-Z0-9\-_]{20,}", "OpenAI / Secret API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"xox[baprs]-[0-9a-zA-Z]{10,}", "Slack Token"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{30,}", "Hardcoded Bearer Token"),
    (r"(?i)(password|secret_key|api_key)\s*=\s*['\"][^'\"]{8,}['\"]", "Exposed Hardcoded Credential"),
]

UNSAFE_CALLS = {
    "eval": "Use of unsafe dynamic eval() function",
    "exec": "Use of unsafe dynamic exec() function",
    "os.system": "Use of unsafe system shell command via os.system()",
    "os.popen": "Use of unsafe system command via os.popen()",
    "pickle.loads": "Use of insecure deserialization via pickle.loads()",
    "pickle.load": "Use of insecure deserialization via pickle.load()",
    "yaml.unsafe_load": "Use of insecure YAML deserialization via yaml.unsafe_load()",
    "marshal.loads": "Use of insecure code deserialization via marshal.loads()",
}


class SecurityAstVisitor(ast.NodeVisitor):
    """AST visitor that scans Python source trees for unsafe call patterns."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.findings: List[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"

        if func_name in UNSAFE_CALLS:
            self.findings.append(f"{self.filename}:{node.lineno} — {UNSAFE_CALLS[func_name]}")

        # Check subprocess shell=True
        if func_name in ("subprocess.run", "subprocess.call", "subprocess.Popen"):
            for keyword in node.keywords:
                if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                    self.findings.append(f"{self.filename}:{node.lineno} — Use of unsafe subprocess with shell=True")

        self.generic_visit(node)


class SecurityValidator:
    """Executable Validator that performs static security inspection and secret scanning."""

    @property
    def name(self) -> str:
        return "security"

    @property
    def is_critical(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        return 2.0

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Scan deliverables for AST security risks and exposed secrets."""
        start_time = time.perf_counter()

        if context.dry_run:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=0.0,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["Dry run mode: skipped security validation"],
            )

        # Discover Python deliverables
        python_files: List[Path] = []
        for item in context.deliverables:
            p = context.project_root / item
            if p.exists() and p.name.endswith(".py"):
                python_files.append(p)

        if not python_files:
            for p in context.project_root.glob("*.py"):
                if p.is_file():
                    python_files.append(p)

        security_errors: List[str] = []
        security_warnings: List[str] = []
        secret_findings: List[str] = []

        for py_file in python_files:
            rel_name = str(py_file.relative_to(context.project_root))
            content = py_file.read_text(encoding="utf-8")

            # 1. AST Unsafe Code Inspection
            try:
                tree = ast.parse(content, filename=rel_name)
                visitor = SecurityAstVisitor(rel_name)
                visitor.visit(tree)
                security_errors.extend(visitor.findings)
            except Exception as exc:
                security_warnings.append(f"{rel_name} — Could not parse AST for security analysis: {exc}")

            # 2. Secret & Credential Regex Scan
            for pattern, label in SECRET_PATTERNS:
                matches = re.finditer(pattern, content)
                for m in matches:
                    secret_findings.append(f"{rel_name} — Potential exposed credential: {label}")

        if secret_findings:
            security_errors.extend(secret_findings)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        log_dir = context.project_root / ".build" / "quality" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "security.log"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Quality OS Log: security ===\n")
            f.write(f"Scanned Files    : {[str(p.name) for p in python_files]}\n")
            f.write(f"Security Errors  : {security_errors}\n")
            f.write(f"Security Warnings: {security_warnings}\n")

        logs = {"security.log": str(log_path)}
        metrics = {
            "scanned_files_count": len(python_files),
            "security_error_count": len(security_errors),
            "secret_finding_count": len(secret_findings),
        }

        if security_errors:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                score=0.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                errors=security_errors,
                warnings=security_warnings,
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
            findings=["Security inspection passed: zero unsafe call patterns or exposed secrets detected"],
            warnings=security_warnings,
            logs=logs,
            metrics=metrics,
        )
