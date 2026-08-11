"""
Unit tests for Executive Decision Layer (Phase B3).
"""


from ape.business.executive import ExecutiveBoard
from ape.business.registry import BusinessUnitRegistry
from ape.business.units import EngineeringUnit, QAUnit


def test_executive_board_directive_delegation():
    registry = BusinessUnitRegistry()
    registry.register_unit(EngineeringUnit())
    registry.register_unit(QAUnit())

    board = ExecutiveBoard(registry=registry)
    directive = board.issue_directive("Accelerate Q3 Production Build", target_kpi="engineering_velocity")

    res = board.execute_directive(directive, workspace_context=None)

    assert res["status"] == "APPROVED"
    assert res["units_executed"] == 2
    assert len(board.directives_history) == 1
