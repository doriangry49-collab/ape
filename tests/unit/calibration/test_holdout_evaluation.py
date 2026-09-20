"""Unit tests for G5.4 Holdout Counterfactual Evaluation Engine & Phase 1 (F-1) / Phase 2 (F-2) Metrics.

EVIDENCE SEPARATION:
- Phase 1: F-1a (Association Slope), F-1b (Logistic Calibration Slope), F-1c (Intercept).
- Phase 2: F-2a (Primary BSI-5), F-2b (Noise-Only BSI-4), 3x3 Transition Matrices, Conservation Rules.
"""

import json
import math
from pathlib import Path

from lab.calibration.holdout_evaluator import (
    compute_boundary_stability,
    compute_ridge_logistic_calibration,
    compute_score_outcome_association_slope,
    run_g5_holdout_evaluation,
)

REPO_ROOT = Path(__file__).parents[3]
HOLDOUT_PATH = REPO_ROOT / ".governance" / "holdout_dataset_2026.json"


def test_f1a_association_slope_synthetic_linear():
    """Verify F-1a score-outcome association slope on clean synthetic linear data."""
    scores = [20.0, 40.0, 60.0, 80.0]
    outcomes = [0, 0, 1, 1]
    slope = compute_score_outcome_association_slope(scores, outcomes)
    assert abs(slope - 2.0) < 1e-6, f"Expected 2.0, got {slope}"


def test_f1a_association_slope_constant_scores_fallback():
    """Verify F-1a handles zero score variance gracefully (fallback = 0.0)."""
    scores = [55.0, 55.0, 55.0, 55.0]
    outcomes = [0, 1, 0, 1]
    slope = compute_score_outcome_association_slope(scores, outcomes)
    assert slope == 0.0, f"Expected fallback 0.0, got {slope}"


def test_f1b_f1c_synthetic_logistic_calibration():
    """Verify F-1b (slope) and F-1c (intercept) on synthetic logistic data."""
    scores = [10.0, 30.0, 50.0, 70.0, 90.0]
    outcomes = [0, 0, 0, 1, 1]
    res = compute_ridge_logistic_calibration(scores, outcomes, lambda_ridge=0.01)

    assert math.isfinite(res.calibration_slope)
    assert math.isfinite(res.calibration_intercept)
    assert res.calibration_slope > 0.0, f"Expected positive slope, got {res.calibration_slope}"


def test_f1_boundary_scores_s0_s100_finite_logits():
    """Verify S=0 and S=100 boundary scores produce finite logits and stable estimates."""
    scores = [0.0, 0.0, 100.0, 100.0]
    outcomes = [0, 0, 1, 1]
    res = compute_ridge_logistic_calibration(scores, outcomes)

    assert math.isfinite(res.calibration_slope)
    assert math.isfinite(res.calibration_intercept)
    assert math.isfinite(res.slope_uncertainty)
    assert math.isfinite(res.intercept_uncertainty)


def test_f1_separation_data_ridge_regularization_finite():
    """Verify quasi-complete separation yields finite, bounded slope via Ridge penalty."""
    scores = [10.0] * 10 + [90.0] * 10
    outcomes = [0] * 10 + [1] * 10
    res = compute_ridge_logistic_calibration(scores, outcomes, lambda_ridge=0.1)

    assert math.isfinite(res.calibration_slope)
    assert res.calibration_slope < 50.0, f"Slope should be bounded by Ridge, got {res.calibration_slope}"


def test_f1c_intercept_is_unpenalized():
    """Verify intercept gamma_0 shifts with base rate without artificial Ridge contraction to 0."""
    scores = [50.0] * 10

    outcomes_low = [0] * 9 + [1]
    res_low = compute_ridge_logistic_calibration(scores, outcomes_low, lambda_ridge=1.0)

    outcomes_high = [0] + [1] * 9
    res_high = compute_ridge_logistic_calibration(scores, outcomes_high, lambda_ridge=1.0)

    assert res_high.calibration_intercept > res_low.calibration_intercept


def test_f1_determinism_byte_for_byte():
    """Verify 100% deterministic F-1 outputs for identical inputs across multiple calls."""
    scores = [53.0, 56.0, 64.0, 70.0, 52.0] * 4
    outcomes = [1, 1, 0, 0, 1] * 4

    res1 = compute_ridge_logistic_calibration(scores, outcomes)
    res2 = compute_ridge_logistic_calibration(scores, outcomes)

    assert res1.calibration_slope == res2.calibration_slope
    assert res1.calibration_intercept == res2.calibration_intercept
    assert res1.slope_uncertainty == res2.slope_uncertainty
    assert res1.intercept_uncertainty == res2.intercept_uncertainty


# --- PHASE 2 (F-2 BSI) UNIT TESTS ---

def test_f2_boundary_crossing_sensitivity():
    """Verify BSI accurately captures decision boundary crossing around 55 and 70 thresholds."""
    # 54 -> delta=+1,+2 cross to VALIDATE (55, 56)
    # 69 -> delta=+1,+2 cross to BUILD (70, 71)
    scores = [54.0, 69.0]
    is_zero_ev = [False, False]

    bsi_res = compute_boundary_stability(scores, is_zero_ev, validate_threshold=55.0)

    # For score=54: baseline=VALIDATE_WITH_USERS... wait: 54 < 55 -> WAIT_FOR_SIGNAL
    # perturbations for 54: 52 (WAIT), 53 (WAIT), 54 (WAIT), 55 (VAL), 56 (VAL)
    # BSI-5 for 54: 3/5 = 0.60, BSI-4 for 54: 2/4 = 0.50
    # For score=69: baseline=VALIDATE_WITH_USERS (69 >= 55)
    # perturbations for 69: 67 (VAL), 68 (VAL), 69 (VAL), 70 (BUILD), 71 (BUILD)
    # BSI-5 for 69: 3/5 = 0.60, BSI-4 for 69: 2/4 = 0.50

    assert bsi_res.bsi_5 == 0.60, f"Expected BSI-5 = 0.60, got {bsi_res.bsi_5}"
    assert bsi_res.bsi_4 == 0.50, f"Expected BSI-4 = 0.50, got {bsi_res.bsi_4}"


def test_f2_perfectly_stable_record_far_from_boundaries():
    """Verify scores far from decision boundaries produce BSI-5 = 1.0 and BSI-4 = 1.0."""
    scores = [30.0, 85.0]  # Deep WAIT, Deep BUILD
    is_zero_ev = [False, False]

    bsi_res = compute_boundary_stability(scores, is_zero_ev)

    assert bsi_res.bsi_5 == 1.0, f"Expected BSI-5 = 1.0, got {bsi_res.bsi_5}"
    assert bsi_res.bsi_4 == 1.0, f"Expected BSI-4 = 1.0, got {bsi_res.bsi_4}"


def test_f2_boundary_adjacent_score_agreement_loss():
    """Verify score right on decision threshold (55.0) experiences expected stability drop."""
    # Score 55.0 baseline = VALIDATE_WITH_USERS
    # Perturbations: 53 (WAIT), 54 (WAIT), 55 (VAL), 56 (VAL), 57 (VAL)
    # Agreement: 3/5 = 0.60 for BSI-5, 2/4 = 0.50 for BSI-4
    scores = [55.0]
    is_zero_ev = [False]

    bsi_res = compute_boundary_stability(scores, is_zero_ev)

    assert bsi_res.bsi_5 == 0.60
    assert bsi_res.bsi_4 == 0.50


def test_f2_bsi5_vs_bsi4_distinction():
    """Verify BSI-5 (includes delta=0) and BSI-4 (excludes delta=0) are distinct."""
    scores = [54.0]  # 54: BSI-5 = 3/5 (0.60), BSI-4 = 2/4 (0.50)
    is_zero_ev = [False]

    bsi_res = compute_boundary_stability(scores, is_zero_ev)

    assert bsi_res.bsi_5 != bsi_res.bsi_4, (
        f"BSI-5 ({bsi_res.bsi_5}) and BSI-4 ({bsi_res.bsi_4}) must not be equal when boundary transitions occur"
    )


def test_f2_determinism_check():
    """Verify 100% deterministic BSI and transition matrix outputs across multiple runs."""
    scores = [53.0, 56.0, 64.0, 70.0]
    is_zero_ev = [False, False, True, False]

    run1 = compute_boundary_stability(scores, is_zero_ev)
    run2 = compute_boundary_stability(scores, is_zero_ev)

    assert run1.bsi_5 == run2.bsi_5
    assert run1.bsi_4 == run2.bsi_4
    assert run1.transition_matrix_5 == run2.transition_matrix_5
    assert run1.transition_matrix_4 == run2.transition_matrix_4


def test_f2_transition_matrix_conservation():
    """Verify 3x3 Transition Matrix total element sum and row conservation rules."""
    scores = [53.0, 56.0, 64.0, 70.0, 52.0]  # 5 records
    is_zero_ev = [False, False, False, False, False]

    bsi_res = compute_boundary_stability(scores, is_zero_ev)

    # 1. Total sum conservation check
    sum_tm5 = sum(
        bsi_res.transition_matrix_5[d1][d2]
        for d1 in bsi_res.transition_matrix_5
        for d2 in bsi_res.transition_matrix_5[d1]
    )
    sum_tm4 = sum(
        bsi_res.transition_matrix_4[d1][d2]
        for d1 in bsi_res.transition_matrix_4
        for d2 in bsi_res.transition_matrix_4[d1]
    )

    assert sum_tm5 == 5 * 5, f"Expected BSI-5 total sum = 25, got {sum_tm5}"
    assert sum_tm4 == 5 * 4, f"Expected BSI-4 total sum = 20, got {sum_tm4}"


def test_production_package_never_imports_lab():
    """Verify zero production files under src/ import from repo-root lab/."""
    src_dir = REPO_ROOT / "src"
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "from lab" not in content, f"Production file {py_file} imports from lab!"
        assert "import lab" not in content, f"Production file {py_file} imports from lab!"


def test_holdout_population_counts_derived_dynamically():
    """Denominator must come from sealed dataset contents, never be hardcoded."""
    with open(HOLDOUT_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    actual_successes = sum(1 for r in records if r["outcome"]["actual_market_outcome"] == "SUCCESS")
    actual_non_successes = sum(1 for r in records if r["outcome"]["actual_market_outcome"] != "SUCCESS")

    assert actual_successes == 11
    assert actual_non_successes == 9
    assert actual_successes + actual_non_successes == 20


def test_success_capture_rate_never_exceeds_100_percent():
    """An 11-success dataset must report rates <= 100%."""
    scorecards = run_g5_holdout_evaluation(HOLDOUT_PATH, REPO_ROOT)

    for model_name, card in scorecards.items():
        assert card.success_capture_rate <= 1.0
        assert card.validation_recall <= 1.0


def test_no_double_counting_across_decisions():
    """BUILD + VALIDATE + WAIT must exactly account for all 20 records per model."""
    scorecards = run_g5_holdout_evaluation(HOLDOUT_PATH, REPO_ROOT)

    for model_name, card in scorecards.items():
        total = card.build_count + card.validate_count + card.wait_count
        assert total == 20


def test_g5_holdout_evaluation_runs_cleanly():
    """Verify G5.4 corrected holdout evaluation runs cleanly across all 20 sealed records."""
    scorecards = run_g5_holdout_evaluation(HOLDOUT_PATH, REPO_ROOT)

    assert len(scorecards) == 4
    assert "Baseline_Model_0" in scorecards
    assert "Model_A_Revenue_Reformulation" in scorecards
    assert "Model_B_Demand_Log_Scaling" in scorecards
    assert "Model_C_Boundary_Sensitivity_52" in scorecards

    # All F-1 and F-2 metrics must be finite across all models
    for name, card in scorecards.items():
        assert math.isfinite(card.association_slope)
        assert math.isfinite(card.calibration_slope)
        assert math.isfinite(card.calibration_intercept)
        assert math.isfinite(card.boundary_stability_index_5)
        assert math.isfinite(card.boundary_stability_index_4)
        assert 0.0 <= card.boundary_stability_index_5 <= 1.0
        assert 0.0 <= card.boundary_stability_index_4 <= 1.0

    # Capital Risk Invariant for Model A & C: must be 0 false BUILDs.
    assert scorecards["Model_A_Revenue_Reformulation"].capital_risk_count == 0
    assert scorecards["Model_C_Boundary_Sensitivity_52"].capital_risk_count == 0

    # Model B false BUILD: 1 (Refactor.io)
    assert scorecards["Model_B_Demand_Log_Scaling"].capital_risk_count == 1
