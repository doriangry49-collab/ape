import hashlib
import json
import uuid
from pathlib import Path

from ape.intelligence.decision.constitution import ConstitutionValidator
from ape.intelligence.decision.models import DecisionReport
from ape.intelligence.decision.scorer import Scorer, load_weights
from ape.utils import append_to_evidence, get_current_artifact


class DecisionEngine:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.weights = load_weights(project_root)
        self.scorer = Scorer(self.weights)
        self.validator = ConstitutionValidator()

    def run_decision(self, topic: str, topic_slug: str) -> DecisionReport:
        """
        Reads the current-state research artifact (O(1) canonical pointer),
        scores it, validates against the Constitution, and saves:
          - Current state  -> .build/decisions/<slug>.json  (mutable)
          - Evidence log   -> .governance/evidence/decisions.jsonl  (append-only)
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
        confidence = int(research_data.get("confidence", 50))

        overall_score, vector_scores, rationale = self.scorer.score(research_data)
        decision, policy, next_step = self.validator.validate(overall_score, vector_scores)

        decision_id = f"dec_{uuid.uuid4().hex[:8]}"

        report = DecisionReport(
            decision_id=decision_id,
            research_id=research_id,
            evidence_hash=evidence_hash,
            topic=topic,
            overall_score=overall_score,
            confidence=confidence,
            decision=decision,
            policy=policy,
            vector_scores=vector_scores,
            rationale=rationale,
            next_step=next_step,
            metadata={"version": "1.0", "generator": "ape-decision-engine"}
        )

        self._save_artifacts(topic_slug, report)
        return report

    def _save_artifacts(self, topic_slug: str, report: DecisionReport) -> None:
        """
        Current state  -> .build/decisions/<slug>.json   (mutable, overwritten)
        Immutable log  -> .governance/evidence/decisions.jsonl  (append-only)
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
        md_content = [
            f"# Decision Report: {report.topic}",
            f"**Decision:** {report.decision}",
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
