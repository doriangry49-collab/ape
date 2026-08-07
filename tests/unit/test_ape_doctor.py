"""
Unit tests for ApeDoctor diagnostics (EPIC 7A-3).
"""

from pathlib import Path
import pytest

from ape.doctor import ApeDoctor


def test_ape_doctor_diagnostics(tmp_path: Path):
    doctor = ApeDoctor(tmp_path)
    checks = doctor.run_all_checks()

    assert len(checks) >= 4
    py_check = next(c for c in checks if c.check_name == "Python Version")
    assert py_check.status == "PASS"

    ws_check = next(c for c in checks if c.check_name == "Workspace Environment")
    assert ws_check.status == "PASS"
