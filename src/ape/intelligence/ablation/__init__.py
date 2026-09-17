"""ORION G3b.3a Ablation & Representation Contract Package."""

from ape.intelligence.ablation.representation_contract import (
    FeatureRubricLevel,
    FeatureRubric,
    R1Representation,
    R2Representation,
    R3Representation,
    RepresentationContract,
    TargetIsolationViolationError,
    extract_r2_features_isolated,
    map_r2_to_scorer_v1_input,
)

__all__ = [
    "FeatureRubricLevel",
    "FeatureRubric",
    "R1Representation",
    "R2Representation",
    "R3Representation",
    "RepresentationContract",
    "TargetIsolationViolationError",
    "extract_r2_features_isolated",
    "map_r2_to_scorer_v1_input",
]
