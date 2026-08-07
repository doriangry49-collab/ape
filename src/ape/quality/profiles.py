"""
Quality OS Profiles & Policy Management — RFC-022 / PR-H1 Specification.
Defines QualityProfile Enum (FAST, STANDARD, STRICT, RELEASE) and validator resolution rules.
"""

from enum import Enum
from typing import Union


class QualityProfile(str, Enum):
    """Quality validation profile determining active validators and strictness gates."""
    FAST = "fast"
    STANDARD = "standard"
    STRICT = "strict"
    RELEASE = "release"

    @classmethod
    def from_str(cls, value: Union[str, "QualityProfile"]) -> "QualityProfile":
        if isinstance(value, QualityProfile):
            return value
        val_lower = str(value).strip().lower()
        for profile in cls:
            if profile.value == val_lower:
                return profile
        raise ValueError(f"Unknown QualityProfile '{value}'. Valid profiles: {[p.value for p in cls]}")


# Normalization map from class names / raw names to canonical short names
VALIDATOR_NAME_MAP: dict[str, str] = {
    "syntaxvalidator": "syntax",
    "importvalidator": "import",
    "dependencyvalidator": "dependency",
    "packagingvalidator": "packaging",
    "securityvalidator": "security",
    "pytestvalidator": "pytest",
    "smokevalidator": "smoke",
    "runtimevalidator": "runtime",
    "replayvalidator": "replay",
    "sbomvalidator": "sbom",
}


def normalize_validator_name(name: str) -> str:
    """Normalize validator class name or raw name to canonical short identifier."""
    raw = str(name).strip().lower()
    return VALIDATOR_NAME_MAP.get(raw, raw)


# Canonical short names per profile
PROFILE_VALIDATOR_MAP: dict[QualityProfile, set[str]] = {
    QualityProfile.FAST: {
        "syntax",
        "import",
        "packaging",
    },
    QualityProfile.STANDARD: {
        "syntax",
        "import",
        "packaging",
        "pytest",
        "smoke",
        "runtime",
    },
    QualityProfile.STRICT: {
        "syntax",
        "import",
        "dependency",
        "packaging",
        "pytest",
        "smoke",
        "runtime",
        "security",
    },
    QualityProfile.RELEASE: {
        "syntax",
        "import",
        "dependency",
        "packaging",
        "pytest",
        "smoke",
        "runtime",
        "security",
        "replay",
        "sbom",
    },
}

# Standardized validator weight breakdown for explainability formula
VALIDATOR_WEIGHTS: dict[str, float] = {
    "syntax": 10.0,
    "import": 10.0,
    "dependency": 10.0,
    "packaging": 15.0,
    "pytest": 20.0,
    "security": 20.0,
    "runtime": 15.0,
    "smoke": 10.0,
    "replay": 15.0,
    "sbom": 10.0,
}


def get_profile_validators(profile: Union[str, QualityProfile]) -> set[str]:
    """Return the set of canonical short validator names active for a given QualityProfile."""
    prof = QualityProfile.from_str(profile)
    return set(PROFILE_VALIDATOR_MAP.get(prof, PROFILE_VALIDATOR_MAP[QualityProfile.STRICT]))


def get_validator_weight(validator_name: str) -> float:
    """Return configured weight for a specific validator."""
    canonical = normalize_validator_name(validator_name)
    return VALIDATOR_WEIGHTS.get(canonical, 10.0)
