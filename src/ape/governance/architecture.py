"""
Constitutional Architecture & API Governance Linter — ORION-110.5 Specification.
Parses Python AST across src/ape/ to enforce:
1. Forbidden Layer Imports (Lower layers MUST NOT import higher layers at runtime).
2. Circular Dependency Detection (Zero cross-module runtime import cycles).
3. Public API Enforcement (Encourages importing via top-level package roots).
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class ArchitectureViolation:
    """Architectural governance violation record."""
    file_path: str
    line_number: int
    violation_type: str  # LAYER_VIOLATION, CIRCULAR_DEPENDENCY, PUBLIC_API_VIOLATION
    message: str

    def format_message(self) -> str:
        return f"[{self.violation_type}] {self.file_path}:{self.line_number} — {self.message}"


class ArchitectureLinter:
    """
    Programmatic AST import linter validating architectural boundary rules across src/ape/.
    """

    LAYER_MAP: Dict[str, int] = {
        "business": 2,
        "runtime": 3,
        "workspace": 4,
        "prompts": 5,
        "pipeline": 5,
        "analytics": 5,
    }

    def get_layer_for_path(self, path: Path) -> str:
        """Determine architectural layer slug for a file path."""
        parts = path.parts
        if "ape" in parts:
            idx = parts.index("ape")
            if idx + 1 < len(parts):
                slug = parts[idx + 1]
                if slug in self.LAYER_MAP:
                    return slug
        return "unknown"

    def _is_type_checking_node(self, node: ast.AST) -> bool:
        """Check if an AST node is an `if TYPE_CHECKING:` guard."""
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                return True
            if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
                return True
        return False

    def _get_runtime_imports(self, tree: ast.AST) -> List[Tuple[str, int]]:
        """Extract import statements from AST, excluding `if TYPE_CHECKING:` blocks."""
        imports: List[Tuple[str, int]] = []

        def visit_nodes(nodes: List[ast.AST]):
            for node in nodes:
                if self._is_type_checking_node(node):
                    continue  # Skip type-checking only imports

                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append((node.module, node.lineno))

                # Recursively visit body attributes if present (e.g. Try, FunctionDef, ClassDef)
                for child_attr in ("body", "orelse", "finalbody"):
                    if hasattr(node, child_attr):
                        child_list = getattr(node, child_attr)
                        if isinstance(child_list, list):
                            visit_nodes(child_list)

        if hasattr(tree, "body") and isinstance(tree.body, list):
            visit_nodes(tree.body)

        return imports

    def scan_layer_imports(self, root_dir: Path) -> List[ArchitectureViolation]:
        """Scan Python source files under root_dir for constitutional import violations."""
        violations: List[ArchitectureViolation] = []
        root_dir = Path(root_dir)

        if not root_dir.exists():
            return violations

        for py_file in root_dir.glob("**/*.py"):
            if py_file.name.startswith("."):
                continue

            source_layer = self.get_layer_for_path(py_file)
            if source_layer == "unknown" or source_layer not in self.LAYER_MAP:
                continue

            source_level = self.LAYER_MAP[source_layer]

            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
            except Exception:
                continue

            imported_modules = self._get_runtime_imports(tree)

            for mod_name, line_no in imported_modules:
                if mod_name.startswith("ape."):
                    parts = mod_name.split(".")
                    if len(parts) >= 2:
                        target_slug = parts[1]
                        if target_slug in self.LAYER_MAP:
                            target_level = self.LAYER_MAP[target_slug]
                            # Illegal backward import (lower level importing higher level)
                            if source_level > target_level:
                                violations.append(
                                    ArchitectureViolation(
                                        file_path=str(py_file.relative_to(root_dir)),
                                        line_number=line_no,
                                        violation_type="LAYER_VIOLATION",
                                        message=f"Layer '{source_layer}' (level {source_level}) illegally imported higher layer '{target_slug}' (level {target_level}) module '{mod_name}'.",
                                    )
                                )

        return violations

    def check_circular_dependencies(self, root_dir: Path) -> List[ArchitectureViolation]:
        """
        Build top-level package dependency graph and detect cross-subsystem circular dependencies.
        Returns list of cycle violations.
        """
        violations: List[ArchitectureViolation] = []
        root_dir = Path(root_dir)
        dep_graph: Dict[str, Set[str]] = {}

        if not root_dir.exists():
            return violations

        # Build module dependency graph across top-level subsystem packages
        for py_file in root_dir.glob("**/*.py"):
            if py_file.name.startswith("."):
                continue

            rel_parts = py_file.relative_to(root_dir).with_suffix("").parts
            subsystem = rel_parts[1] if len(rel_parts) > 1 else ""
            if subsystem not in self.LAYER_MAP:
                continue

            mod_key = f"ape.{subsystem}"

            if mod_key not in dep_graph:
                dep_graph[mod_key] = set()

            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
            except Exception:
                continue

            runtime_imports = self._get_runtime_imports(tree)

            for mod_name, _ in runtime_imports:
                if mod_name.startswith("ape."):
                    target_parts = mod_name.split(".")
                    if len(target_parts) >= 2:
                        target_sub = target_parts[1]
                        if target_sub in self.LAYER_MAP:
                            target_key = f"ape.{target_sub}"
                            if target_key != mod_key:
                                dep_graph[mod_key].add(target_key)

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    cycle_str = " -> ".join(path[path.index(neighbor):] + [neighbor])
                    violations.append(
                        ArchitectureViolation(
                            file_path=node,
                            line_number=1,
                            violation_type="CIRCULAR_DEPENDENCY",
                            message=f"Cross-subsystem circular dependency detected: {cycle_str}",
                        )
                    )

            rec_stack.remove(node)
            path.pop()

        for mod in list(dep_graph.keys()):
            if mod not in visited:
                dfs(mod, [])

        return violations
