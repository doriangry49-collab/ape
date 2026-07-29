from ape.intelligence.decision.constitution import ConstitutionValidator


def test_high_score_without_evidence_blocks_go():
    # Arrange
    validator = ConstitutionValidator()
    overall_score = 95  # Very high numeric score
    evidence_flags = {
        "payment_signal": "UNKNOWN",
        "identifiable_customer": True,
        "ai_solvability": True
    }
    
    # Act
    decision = validator.evaluate_business_gate(overall_score, evidence_flags)
    
    # Assert
    assert decision.policy != "BUILD"  # Cannot be GO
    assert decision.policy in ["VALIDATE", "WATCH"]


def test_low_score_with_evidence_does_not_go():
    validator = ConstitutionValidator()
    overall_score = 40  # Low score
    evidence_flags = {
        "payment_signal": True,
        "identifiable_customer": True,
        "ai_solvability": True
    }
    
    decision = validator.evaluate_business_gate(overall_score, evidence_flags)
    assert decision.policy != "BUILD"


def test_high_score_with_full_evidence_is_go():
    validator = ConstitutionValidator()
    overall_score = 85
    evidence_flags = {
        "payment_signal": True,
        "identifiable_customer": True,
        "ai_solvability": True
    }
    
    decision = validator.evaluate_business_gate(overall_score, evidence_flags)
    assert decision.policy == "BUILD"
