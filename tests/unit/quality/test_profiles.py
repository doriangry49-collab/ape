"""
Unit tests for Quality OS Profiles (PR-H1).
"""

from pathlib import Path
import pytest

from ape.quality.contracts import ValidationContext, ValidationStatus
from ape.quality.profiles import QualityProfile, get_profile_validators, get_validator_weight
from ape.quality.runner import QualityRunner


def test_quality_profile_enum_parsing():
    assert QualityProfile.from_str("fast") == QualityProfile.FAST
    assert QualityProfile.from_str("STANDARD") == QualityProfile.STANDARD
    assert QualityProfile.from_str("Strict") == QualityProfile.STRICT
    assert QualityProfile.from_str("release") == QualityProfile.RELEASE

    with pytest.raises(ValueError, match="Unknown QualityProfile"):
        QualityProfile.from_str("ultra_strict")


def test_profile_validators_mapping():
    fast_validators = get_profile_validators("fast")
    assert fast_validators == {"syntax", "import", "packaging"}
    assert "pytest" not in fast_validators
    assert "security" not in fast_validators

    standard_validators = get_profile_validators("standard")
    assert {"syntax", "import", "packaging", "pytest", "smoke", "runtime"}.issubset(standard_validators)
    assert "security" not in standard_validators

    strict_validators = get_profile_validators("strict")
    assert "security" in strict_validators
    assert "dependency" in strict_validators

    release_validators = get_profile_validators("release")
    assert "replay" in release_validators
    assert "sbom" in release_validators


def test_validator_weights():
    assert get_validator_weight("syntax") == 10.0
    assert get_validator_weight("pytest") == 20.0
    assert get_validator_weight("security") == 20.0
    assert get_validator_weight("unknown_val") == 10.0


def test_quality_runner_profile_filtering(tmp_path: Path):
    context = ValidationContext(
        project_root=tmp_path,
        topic_slug="test_topic",
        deliverables=["main.py"],
        dry_run=True,
        quality_profile="fast",
    )
    runner = QualityRunner()
    report = runner.run(context)

    assert report.quality_profile == "fast"
    from ape.quality.profiles import normalize_validator_name
    executed_names = {normalize_validator_name(r.validator_name) for r in report.results}
    assert executed_names == {"syntax", "import", "packaging"}
    assert "pytest" not in executed_names
    assert "security" not in executed_names
