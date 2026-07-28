def test_pain_point_extractor_preserves_provenance():
    from ape.intelligence.scanner.extractor import PainPointExtractor
    
    # Arrange
    raw_text = "Müşteriler WhatsApp mesajlarına yetişemediğimiz için şikayetçi."
    extractor = PainPointExtractor()
    
    # Act
    pain_point, provenance = extractor.extract(raw_text, source_name="sikayetvar_mock")
    
    # Assert
    assert provenance.source_adapter == "sikayetvar_mock"
    assert provenance.raw_observation == raw_text
    assert provenance.reference_url is None
    # Extractor MUST NOT fabricate URLs or signals
    assert pain_point.payment_signal == "UNKNOWN"

def test_emlak_asistan_pre_seeded_hypothesis():
    from ape.intelligence.models import UNKNOWN, PainPoint
    
    # Ensure emlak asistanı is seeded without prior scores
    p = PainPoint(
        domain="real_estate",
        description="Emlak asistanı",
        frequency_signal=UNKNOWN,
        payment_signal=UNKNOWN,
        ai_solvable=UNKNOWN
    )
    assert p.payment_signal == UNKNOWN
    assert p.payment_signal != 0  # UNKNOWN is strictly separated from 0
