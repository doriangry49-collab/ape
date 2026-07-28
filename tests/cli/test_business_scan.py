from typer.testing import CliRunner

from ape.cli import app


def test_ape_scan_business_mode_offline():
    runner = CliRunner()
    
    # Act
    # Business mode should run offline mock adapters without network
    result = runner.invoke(app, ["scan", "--mode", "business", "--offline"])
    
    # Assert
    # Test will fail initially because --mode and --offline are not implemented
    assert result.exit_code == 0
    assert "Business Signals" in result.stdout
    assert "Pain Points" in result.stdout
