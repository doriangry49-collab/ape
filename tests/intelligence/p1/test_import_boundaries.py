import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_import_boundaries import audit_production_boundary, check_file_imports


def test_production_has_zero_lab_import_violations():
    """Assert production package (src/ape/) has zero imports from lab."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    src_ape_dir = repo_root / "src" / "ape"
    
    assert src_ape_dir.exists()
    violations = audit_production_boundary(src_ape_dir)
    assert len(violations) == 0, f"Found unexpected boundary violations in production: {violations}"


def test_boundary_checker_detects_forbidden_lab_imports(tmp_path):
    """Assert AST checker detects static import lab and from lab... statements."""
    bad_code = (
        "import os\n"
        "import lab.experiments.exp1\n"
        "from lab.candidates import scanner\n"
        "def foo():\n"
        "    pass\n"
    )
    bad_file = tmp_path / "bad_module.py"
    bad_file.write_text(bad_code, encoding="utf-8")

    violations = check_file_imports(bad_file)
    assert len(violations) == 2
    assert "import lab.experiments.exp1" in violations[0].statement
    assert "from lab.candidates import ..." in violations[1].statement


def test_boundary_checker_detects_dynamic_lab_imports(tmp_path):
    """Assert AST checker detects dynamic __import__('lab') calls."""
    dynamic_code = (
        "import sys\n"
        "mod = __import__('lab.experiments')\n"
    )
    dynamic_file = tmp_path / "dynamic_module.py"
    dynamic_file.write_text(dynamic_code, encoding="utf-8")

    violations = check_file_imports(dynamic_file)
    assert len(violations) == 1
    assert "__import__('lab.experiments')" in violations[0].statement
