# Skill: TDD (Test-Driven Development)

All code implementations must be guided by Test-Driven Development (TDD) principles to prevent regressions and clarify boundaries.

## Red-Green-Refactor Cycle

1. **RED:**
   - Write tests in `tests/test_<feature>.py` before writing production code.
   - Assertions should check the expected interface and output.
   - Run tests (`pytest`) and verify they fail because the implementation does not exist yet.

2. **GREEN:**
   - Write the minimum amount of code required to make the tests pass.
   - Do not implement scope creep or premature optimizations.
   - Run tests and ensure they are all green.

3. **REFACTOR:**
   - Clean up the code.
   - Address long lines (PEP 8/Ruff limit), ensure proper docstrings, type hints, and sort imports.
   - Re-run tests to confirm no regressions were introduced.
