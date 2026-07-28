def test_offline_file_adapter_returns_opportunity():
    from ape.intelligence.scanner.business import OfflineFileAdapter

    from ape.intelligence.models import UNKNOWN, Opportunity, PainPoint
    
    # Arrange
    adapter = OfflineFileAdapter(mock_data_path="dummy_path.json")
    
    # Act
    results = adapter.scan()
    
    # Assert
    assert len(results) > 0
    opp = results[0]
    assert isinstance(opp, Opportunity)
    assert isinstance(opp.pain_point, PainPoint)
    assert opp.pain_point.payment_signal == UNKNOWN  # Ensure UNKNOWN isolation
    assert opp.is_hypothesis is True
