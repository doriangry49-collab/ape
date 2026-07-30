#!/usr/bin/env python3
"""
AST Import Boundary Checker for APE.

Enforces strict isolation between Production (src/ape/) and R&D Lab (lab/).
Invariant: No module under `src/ape/` may import `lab` or any subpackage of `lab`.

Exits 0 if clean, 1 if boundary violation is detected.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


class BoundaryViolation:
    def __init__(self, file_path: Path, line_number: int, statement: str, reason: str) -> None:
        self.file_path = file_path
        self.line_number = line_number
        self.statement = statement
        self.reason = reason

    def __str__(self) -> str:
        return (
            f"VIOLATION in {self.file_path}:{self.line_number}\n"
            f"  Statement : {self.statement}\n"
            f"  Reason    : {self.reason}"
        )


def check_file_imports(file_path: Path) -> list[BoundaryViolation]:
    """Parse a python source file using AST and check for forbidden lab imports."""
    violations: list[BoundaryViolation] = []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as err:
        violations.append(
            BoundaryViolation(
                file_path=file_path,
                line_number=getattr(err, "lineno", 1) or 1,
                statement="<parse error>",
                reason=f"Failed to parse source file: {err}",
            )
        )
        return violations

    for node in ast.walk(tree):
        # 1. Check `import lab` / `import lab.foo`
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "lab" or name.startswith("lab."):
                    violations.append(
                        BoundaryViolation(
                            file_path=file_path,
                            line_number=node.lineno,
                            statement=f"import {name}",
                            reason="Production code (src/ape/) is strictly forbidden from importing R&D lab modules.",
                        )
                    )
        # 2. Check `from lab import foo` / `from lab.bar import baz`
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "lab" or module.startswith("lab."):
                violations.append(
                    BoundaryViolation(
                        file_path=file_path,
                        line_number=node.lineno,
                        statement=f"from {module} import ...",
                        reason="Production code (src/ape/) is strictly forbidden from importing R&D lab modules.",
                    )
                )
        # 3. Check dynamic import calls e.g. `__import__('lab')` or `import_module('lab')`
        elif isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name in ("__import__", "import_module"):
                if node.args and isinstance(node.args[0], ast.Constant):
                    val = str(node.args[0].value)
                    if val == "lab" or val.startswith("lab."):
                        violations.append(
                            BoundaryViolation(
                                file_path=file_path,
                                line_number=node.lineno,
                                statement=f"{func_name}('{val}')",
                                reason="Production code is strictly forbidden from dynamically importing R&D lab modules.",
                            )
                        )

    return violations


def audit_production_boundary(src_dir: Path) -> list[BoundaryViolation]:
    """Scan all python files in production source directory for boundary violations."""
    all_violations: list[BoundaryViolation] = []
    if not src_dir.exists():
        print(f"Warning: Source directory {src_dir} does not exist.")
        return all_violations

    for py_file in src_dir.rglob("*.py"):
        violations = check_file_imports(py_file)
        all_violations.extend(violations)

    return all_violations


def main() -> int:
    # Determine workspace root
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        src_path = Path(sys.argv[1]).resolve()
    else:
        # Default to src/ape
        root_dir = Path(__file__).resolve().parent.parent
        src_path = root_dir / "src" / "ape"

    print(f"Auditing AST Import Boundaries in: {src_path}")
    violations = audit_production_boundary(src_path)

    if violations:
        print("\n========================================================")
        print(f"[ERROR] BOUNDARY VIOLATIONS DETECTED ({len(violations)} found):")
        print("========================================================")
        for v in violations:
            print(v)
            print("-" * 56)
        return 1

    print("\n[OK] SUCCESS: Zero import boundary violations detected. Production (src/ape/) is 100% isolated from lab.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
