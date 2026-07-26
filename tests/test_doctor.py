from typer.testing import CliRunner

from ape.cli import app

runner = CliRunner()


def test_doctor_command_succeeds_and_prints_status() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "APE Environment Status" in result.output
    assert "python" in result.output.lower()
