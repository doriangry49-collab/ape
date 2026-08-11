"""
Unit tests for ORION-110.5 Constitutional Architecture & API Governance.
Verifies AST layer import linter (zero layer violations), cycle detection (zero import cycles),
and frozen public API package exports.
"""

from pathlib import Path

import ape
from ape import (
    CancellationToken,
    CheckpointStore,
    ExecutionOrchestrator,
    ExecutionRuntime,
    MockLLMProvider,
    PromptTemplate,
    RenderedPrompt,
    ReplayEngine,
    RetryPolicy,
    VentureWorkspaceManager,
)
from ape.governance.architecture import ArchitectureLinter


def test_public_api_freeze_exports():
    """Verify frozen public API interface exports in root ape package."""
    assert ape.__version__ == "0.1.0"
    assert ExecutionRuntime is not None
    assert ReplayEngine is not None
    assert CancellationToken is not None
    assert RetryPolicy is not None
    assert CheckpointStore is not None
    assert MockLLMProvider is not None
    assert ExecutionOrchestrator is not None
    assert VentureWorkspaceManager is not None
    assert RenderedPrompt is not None
    assert PromptTemplate is not None


def test_ast_linter_zero_layer_import_violations():
    """Verify AST import linter finds 0 illegal backward layer imports in src/ape/."""
    linter = ArchitectureLinter()
    src_dir = Path(__file__).parents[3] / "src" / "ape"

    violations = linter.scan_layer_imports(src_dir)

    # Output formatted violation messages if any found
    err_msgs = [v.format_message() for v in violations]
    assert len(violations) == 0, f"Found {len(violations)} architectural layer violations:\n" + "\n".join(err_msgs)


def test_ast_linter_zero_circular_dependencies():
    """Verify AST linter detects zero import cycles in src/ape/."""
    linter = ArchitectureLinter()
    src_dir = Path(__file__).parents[3] / "src" / "ape"

    cycle_violations = linter.check_circular_dependencies(src_dir)

    err_msgs = [v.message for v in cycle_violations]
    assert len(cycle_violations) == 0, f"Found {len(cycle_violations)} circular dependency cycles:\n" + "\n".join(err_msgs)
