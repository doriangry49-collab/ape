import hashlib
import json
import uuid
from pathlib import Path
from typing import List

from ape.intelligence.decision.bridge import BridgeResult, InferenceBridge
from ape.intelligence.decision.constitution import ConstitutionValidator
from ape.intelligence.decision.models import DecisionReport
from ape.intelligence.decision.scorer import Scorer, load_weights
from ape.intelligence.models import UNKNOWN, BusinessEvidence, EvidenceProvenance
from ape.utils import append_to_evidence, get_current_artifact


class DecisionEngine:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.weights = load_weights(project_root)
        self.scorer = Scorer(self.weights)
        self.validator = ConstitutionValidator()
        self.bridge = InferenceBridge()

    def run_decision(self, topic: str, topic_slug: str) -> DecisionReport:
        """
        Reads the current-state research artifact (O(1) canonical pointer),
        runs InferenceBridge, evaluates against Constitution Policy Gate, and saves:
          - Current state  -> .build/decisions/<slug>.json  (mutable)
          - Evidence log   -> .governance/evidence/decisions-YYYY-MM.jsonl  (append-only)
        """
        research_dir = self.project_root / ".build" / "research"
        research_file = get_current_artifact(research_dir, topic_slug)

        if not research_file:
            raise FileNotFoundError(
                f"Research report not found for topic: {topic_slug}. "
                "Run `ape research` first."
            )

        with open(research_file, "r", encoding="utf-8") as f:
            raw_content = f.read()
            research_data = json.loads(raw_content)

        evidence_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()

        metadata = research_data.get("metadata", {})
        research_id = metadata.get("research_id", "UNKNOWN")
        conf_raw = research_data.get("confidence", 0.80)
        if isinstance(conf_raw, (int, float)):
            confidence = int(conf_raw * 100) if conf_raw <= 1.0 else int(conf_raw)
        else:
            confidence = 80

        # Aggregate evidence via InferenceBridge
        has_business_data = (
            "business_evidence" in research_data
            or "evidence_items" in research_data
            or "evidence_flags" in research_data
        )

        if has_business_data:
            raw_evidence = research_data.get("business_evidence", []) or research_data.get(
                "evidence_items", []
            )
            evidence_list = []
            for ev in raw_evidence:
                if isinstance(ev, BusinessEvidence):
                    evidence_list.append(ev)
                elif isinstance(ev, dict):
                    prov_dict = ev.get("provenance", {})
                    prov = (
                        EvidenceProvenance(
                            source_adapter=prov_dict.get("source_adapter", "unknown"),
                            raw_observation=prov_dict.get("raw_observation", ""),
                            reference_url=prov_dict.get("reference_url"),
                            request_context=prov_dict.get("request_context"),
                        )
                        if isinstance(prov_dict, dict)
                        else None
                    )
                    if prov:
                        evidence_list.append(
                            BusinessEvidence(
                                search_intent_observation=ev.get(
                                    "search_intent_observation", UNKNOWN
                                ),
                                pain_observation=ev.get("pain_observation", UNKNOWN),
                                manual_work_observation=ev.get("manual_work_observation", UNKNOWN),
                                pricing_observation=ev.get("pricing_observation", UNKNOWN),
                                entity_observation=ev.get("entity_observation", UNKNOWN),
                                competition_observation=ev.get("competition_observation", UNKNOWN),
                                provenance=prov,
                            )
                        )

            bridge_result = self.bridge.aggregate_evidence(evidence_list)

            # Allow direct evidence_flags override in research_data if explicitly provided.
            # WN-2 fix: When no evidence_list is available (pure override path), we MUST NOT
            # silently drop provenance. Instead, represent the override origin explicitly via a
            # synthetic EvidenceProvenance so SPEC-0013 §5 audit lineage is preserved.
            if "evidence_flags" in research_data and not evidence_list:
                override_reference_urls: List[str] = research_data.get("reference_urls", [])
                override_provenance = EvidenceProvenance(
                    source_adapter="evidence_flags_override",
                    raw_observation=(
                        f"Direct evidence_flags override for research_id={research_id}. "
                        "No BusinessEvidence items were present in research artifact."
                    ),
                    reference_url=override_reference_urls[0] if override_reference_urls else None,
                    request_context="DecisionEngine.run_decision:evidence_flags_override",
                )
                bridge_result = BridgeResult(
                    evidence_flags=research_data["evidence_flags"],
                    provenance_chain=[override_provenance],
                    reference_urls=override_reference_urls,
                )
        else:
            bridge_result = BridgeResult(
                evidence_flags={},
                provenance_chain=[],
                reference_urls=[],
            )

        overall_score, vector_scores, rationale = self.scorer.score(research_data)
        gate_result = self.validator.evaluate_policy(
            overall_score, vector_scores, bridge_result=bridge_result
        )

        decision_id = f"dec_{uuid.uuid4().hex[:8]}"

        report = DecisionReport(
            decision_id=decision_id,
            research_id=research_id,
            evidence_hash=evidence_hash,
            topic=topic,
            overall_score=overall_score,
            confidence=confidence,
            decision=gate_result.decision,
            policy=gate_result.policy_code,
            vector_scores=vector_scores,
            rationale=rationale,
            next_step=gate_result.message,
            evidence_flags=bridge_result.evidence_flags,
            provenance_chain=bridge_result.provenance_chain,
            reference_urls=bridge_result.reference_urls,
            metadata={"version": "1.1", "generator": "ape-decision-engine"},
        )

        self._save_artifacts(topic_slug, report)
        return report

    def _save_artifacts(self, topic_slug: str, report: DecisionReport) -> None:
        """
        Current state  -> .build/decisions/<slug>.json   (mutable, overwritten)
        Immutable log  -> .governance/evidence/decisions-YYYY-MM.jsonl  (append-only)
        """
        decisions_dir = self.project_root / ".build" / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)

        report_dict = report.to_dict()

        # 1. Current state (canonical pointer - mutable)
        json_path = decisions_dir / f"{topic_slug}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        # 2. Evidence history (append-only)
        evidence_dir = self.project_root / ".governance" / "evidence"
        append_to_evidence(evidence_dir, "decisions", report_dict)

        # 3. Markdown (current state - mutable)
        md_path = decisions_dir / f"{topic_slug}.md"
        dec_str = report.decision.value if hasattr(report.decision, "value") else str(report.decision)
        md_content = [
            f"# Decision Report: {report.topic}",
            f"**Decision:** {dec_str}",
            f"**Policy:** {report.policy}",
            f"**Overall Score:** {report.overall_score} / 100",
            f"**Confidence in Data:** {report.confidence}%",
            f"**Next Step:** {report.next_step}",
            "",
            "## Score Breakdown",
        ]
        for line in report.rationale:
            md_content.append(f"- {line}")

        md_content.extend([
            "",
            "## Evidence Trace",
            f"- **Research ID:** `{report.research_id}`",
            f"- **Decision ID:** `{report.decision_id}`",
            f"- **Evidence Hash:** `{report.evidence_hash}`",
        ])

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

