"""
Unit tests for Quality OS Validators and Registry Engine.
"""

from pathlib import Path
import tempfile
import pytest

from ape.quality.contracts import ValidationContext, ValidationStatus
from ape.quality.registry import ValidatorRegistry
from ape.quality.validators.syntax import SyntaxValidator
from ape.quality.validators.import_validator import ImportValidator


def test_syntax_validator_valid_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        py_file = root / "valid_module.py"
        py_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

        val = SyntaxValidator()
        assert val.is_critical is True
        assert val.weight == 2.0
        ctx = ValidationContext(project_root=root, topic_slug="test_topic", deliverables=["valid_module.py"])
        res = val.validate(ctx)

        assert res.status == ValidationStatus.PASS
        assert res.score == 100.0
        assert len(res.errors) == 0


def test_syntax_validator_invalid_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        py_file = root / "broken_module.py"
        py_file.write_text("def broken(:\n    return world\n", encoding="utf-8")

        val = SyntaxValidator()
        ctx = ValidationContext(project_root=root, topic_slug="test_topic", deliverables=["broken_module.py"])
        res = val.validate(ctx)

        assert res.status == ValidationStatus.FAIL
        assert res.score == 0.0
        assert len(res.errors) > 0


def test_import_validator_valid_module():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        py_file = root / "importable.py"
        py_file.write_text("VALUE = 42\n", encoding="utf-8")

        val = ImportValidator()
        assert val.is_critical is True
        assert val.weight == 1.5
        ctx = ValidationContext(project_root=root, topic_slug="test_topic", deliverables=["importable.py"])
        res = val.validate(ctx)

        assert res.status == ValidationStatus.PASS
        assert res.score == 100.0
        assert len(res.errors) == 0


def test_validator_registry_discovery():
    registry = ValidatorRegistry()
    python_validators = registry.discover("python")
    assert len(python_validators) >= 2
    names = [v.name for v in python_validators]
    assert "SyntaxValidator" in names
    assert "ImportValidator" in names
