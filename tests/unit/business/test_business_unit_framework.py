"""
Unit tests for Business Unit Framework (Phase B1).
"""


from ape.business.contracts import BusinessUnit
from ape.business.registry import BusinessUnitRegistry
from ape.business.units import EngineeringUnit, QAUnit


def test_business_unit_protocol_compliance():
    eng_unit = EngineeringUnit()
    assert isinstance(eng_unit, BusinessUnit)
    assert eng_unit.name == "engineering_unit"
    assert "engineering_velocity" in eng_unit.kpis


def test_business_unit_registry():
    registry = BusinessUnitRegistry()
    eng_unit = EngineeringUnit()
    qa_unit = QAUnit()

    registry.register_unit(eng_unit)
    registry.register_unit(qa_unit)

    assert registry.get_unit("engineering_unit") is not None
    assert len(registry.list_all_units()) == 2
