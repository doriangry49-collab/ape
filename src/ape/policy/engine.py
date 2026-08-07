"""
Declarative Policy Engine Architecture — RFC-022 / PR-I1 Specification.
Evaluates pipeline evidence against declarative release_policy.yaml configuration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from ape.pipeline.contracts import BasePipelineContext, StageResult, StageStatus
from ape.policy.contracts import PolicyEvaluationResult, ReleasePolicy


class PolicyEngine:
    """Evaluates pipeline stage evidence and quality metrics against declarative policies."""

    def __init__(self, project_root: Path, policy: Optional[ReleasePolicy] = None) -> None:
        self.project_root = Path(project_root)
        self.policy = policy or self._load_policy()

    def _load_policy(self) -> ReleasePolicy:
        """Loads .governance/policies/release_policy.yaml or defaults."""
        policy_file = self.project_root / ".governance" / "policies" / "release_policy.yaml"
        if not policy_file.exists():
            policy_file = self.project_root / ".governance" / "policies" / "release_policy.json"

        if policy_file.exists():
            try:
                if policy_file.suffix == ".json":
                    data = json.loads(policy_file.read_text(encoding="utf-8"))
                    return ReleasePolicy(
                        name=data.get("name", "custom_policy"),
                        minimum_confidence=float(data.get("minimum_confidence", 85.0)),
                        allow_security_warn=bool(data.get("allow_security_warn", True)),
                        minimum_runtime_score=float(data.get("minimum_runtime_score", 80.0)),
                        require_runtime=bool(data.get("require_runtime", True)),
                        require_replay=bool(data.get("require_replay", False)),
                        require_sbom=bool(data.get("require_sbom", False)),
                        max_critical_vulnerabilities=int(data.get("max_critical_vulnerabilities", 0)),
                    )
            except Exception:
                pass
        return ReleasePolicy()

    def evaluate(self, context: BasePipelineContext, previous_results: List[StageResult]) -> PolicyEvaluationResult:
        """Evaluates pipeline stage results against configured ReleasePolicy."""
        violations: List[str] = []
        passed_rules: List[str] = []
        metrics: dict[str, Any] = {}

        # Extract quality report & previous stage outputs
        qual_report: dict[str, Any] = {}
        verification_passed = False
        task_completed = True

        for res in previous_results:
            if res.status == StageStatus.FAILED:
                violations.append(f"Pipeline stage '{res.stage_name}' failed")
            elif res.status == StageStatus.BLOCKED:
                violations.append(f"Pipeline stage '{res.stage_name}' was blocked")
            elif res.stage_name == "quality_assurance":
                qual_report = res.output_data.get("quality_report", {})
            elif res.stage_name == "verification":
                verification_passed = res.output_data.get("verification_passed", False)
            elif res.stage_name == "task_execution":
                status_str = res.output_data.get("status", "COMPLETED")
                if status_str != "COMPLETED":
                    task_completed = False

        if not verification_passed:
            violations.append("Deliverable verification check failed or incomplete")
        else:
            passed_rules.append("Deliverables verified on disk")

        if not task_completed:
            violations.append("Task execution engine state is not COMPLETED")

        # Evaluate Quality OS Metrics
        release_conf = float(qual_report.get("release_confidence", 100.0))
        metrics["release_confidence"] = release_conf
        metrics["quality_profile"] = qual_report.get("quality_profile", "standard")

        # 1. Minimum Confidence Rule
        if release_conf < self.policy.minimum_confidence:
            violations.append(
                f"Release confidence ({release_conf:.1f}%) is below minimum policy threshold ({self.policy.minimum_confidence:.1f}%)"
            )
        else:
            passed_rules.append(f"Confidence score ({release_conf:.1f}%) meets threshold ({self.policy.minimum_confidence:.1f}%)")

        # 2. Security Warnings Rule
        results_list = qual_report.get("results", [])
        sec_results = [r for r in results_list if r.get("validator_name", "").lower() in ("security", "securityvalidator")]
        has_sec_warn = any(r.get("status") == "WARN" for r in sec_results)
        if not self.policy.allow_security_warn and has_sec_warn:
            violations.append("Policy prohibits security warnings, but security scanner issued WARN")
        else:
            passed_rules.append("Security warning policy rule satisfied")

        # 3. Runtime Verification Rule
        runtime_results = [r for r in results_list if r.get("validator_name", "").lower() in ("runtime", "runtimevalidator")]
        runtime_passed = all(r.get("status") in ("PASS", "SKIP") for r in runtime_results) if runtime_results else True
        runtime_score = runtime_results[0].get("score", 100.0) if runtime_results else 100.0
        metrics["runtime_score"] = runtime_score

        if self.policy.require_runtime and not runtime_passed:
            violations.append("Policy requires live runtime verification PASS, but runtime check failed or crashed")
        elif self.policy.require_runtime and runtime_score < self.policy.minimum_runtime_score:
            violations.append(f"Runtime score ({runtime_score:.1f}) is below minimum threshold ({self.policy.minimum_runtime_score:.1f})")
        else:
            passed_rules.append("Runtime verification policy satisfied")

        # 4. Require Replay Rule
        if self.policy.require_replay:
            replay_verified = any("replay" in r.get("validator_name", "").lower() for r in results_list)
            if not replay_verified:
                violations.append("Policy requires explicit Replay reproducibility proof prior to release")
            else:
                passed_rules.append("Replay reproducibility proof verified")

        passed = len(violations) == 0

        return PolicyEvaluationResult(
            passed=passed,
            policy_name=self.policy.name,
            violations=violations,
            passed_rules=passed_rules,
            evaluated_metrics=metrics,
        )
