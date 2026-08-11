"""
Unit tests for Quality Trend Engine (PR-J1).
"""

from pathlib import Path

from ape.analytics.trend import QualityTrendEngine, QualityTrendReport


def test_quality_trend_engine_analysis(tmp_path: Path):
    engine = QualityTrendEngine(tmp_path)
    report = engine.analyze_trend("Calculator App")

    assert isinstance(report, QualityTrendReport)
    assert report.topic_slug == "calculator_app"
    assert report.total_builds >= 1
    assert report.direction in ("IMPROVING", "DEGRADED", "STABLE")


def test_quality_trend_cli_rendering(tmp_path: Path):
    engine = QualityTrendEngine(tmp_path)
    report = engine.analyze_trend("Calculator App")
    cli_text = engine.render_cli(report)

    assert "Quality Trend Report" in cli_text
    assert "Trajectory" in cli_text.title() or "TRAJECTORY" in cli_text
