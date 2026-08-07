"""
Declarative Policy Engine Data Contracts — RFC-022 / PR-I1 Specification.
Defines ReleasePolicy and PolicyEvaluationResult data structures.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ReleasePolicy:
    """Declarative policy configuration loaded from YAML or defaults."""
    name: str = "default_release_policy"
    minimum_confidence: float = 85.0
    allow_security_warn: bool = True
    minimum_runtime_score: float = 80.0
    require_runtime: bool = True
    require_replay: bool = False
    require_sbom: bool = False
    max_critical_vulnerabilities: int = 0
    required_profiles: List[str] = field(default_factory=lambda: ["standard", "strict", "release"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "minimum_confidence": self.minimum_confidence,
            "allow_security_warn": self.allow_security_warn,
            "minimum_runtime_score": self.minimum_runtime_score,
            "require_runtime": self.require_runtime,
            "require_replay": self.require_replay,
            "require_sbom": self.require_sbom,
            "max_critical_vulnerabilities": self.max_critical_vulnerabilities,
            "required_profiles": self.required_profiles,
        }


@dataclass
class PolicyEvaluationResult:
    """Outcome of PolicyEngine evaluation against pipeline state and evidence."""
    passed: bool
    policy_name: str
    violations: List[str] = field(default_factory=list)
    passed_rules: List[str] = field(default_factory=list)
    evaluated_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "policy_name": self.policy_name,
            "violations": self.violations,
            "passed_rules": self.passed_rules,
            "evaluated_metrics": self.evaluated_metrics,
        }
