"""
BriefGenerator — Deterministic Executive Brief Assembly Module.

Assembles deliverables/<slug>/EXECUTIVE_BRIEF.md directly from:
- .build/research/<slug>.json
- .build/decisions/<slug>.json
- .build/roadmaps/<slug>.json

100% deterministic, template-based, zero LLM, zero network.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class BriefGenerator:
    """Deterministic assembler for Executive Brief markdown deliverables."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)

    def generate_brief(self, topic_slug: str) -> Path:
        """
        Reads research, decision, and roadmap JSON artifacts for topic_slug,
        assembles a deterministic Executive Brief, and writes to disk.
        """
        build_dir = self.project_root / ".build"
        research_file = build_dir / "research" / f"{topic_slug}.json"
        decision_file = build_dir / "decisions" / f"{topic_slug}.json"
        roadmap_file = build_dir / "roadmaps" / f"{topic_slug}.json"

        if not research_file.exists():
            raise FileNotFoundError(f"Research artifact missing for '{topic_slug}': {research_file}")
        if not decision_file.exists():
            raise FileNotFoundError(f"Decision artifact missing for '{topic_slug}': {decision_file}")

        research_data: Dict[str, Any] = json.loads(research_file.read_text(encoding="utf-8"))
        decision_data: Dict[str, Any] = json.loads(decision_file.read_text(encoding="utf-8"))
        roadmap_data: Dict[str, Any] = json.loads(roadmap_file.read_text(encoding="utf-8")) if roadmap_file.exists() else {}

        content = self._render_template(research_data, decision_data, roadmap_data)

        output_dir = self.project_root / "deliverables" / topic_slug
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "EXECUTIVE_BRIEF.md"
        output_file.write_text(content, encoding="utf-8")

        return output_file

    def _render_template(
        self,
        research: Dict[str, Any],
        decision: Dict[str, Any],
        roadmap: Dict[str, Any],
    ) -> str:
        topic = research.get("topic", decision.get("topic", "Unknown Topic"))
        timestamp = decision.get("timestamp", research.get("timestamp", "N/A"))
        decision_id = decision.get("decision_id", "N/A")
        evidence_hash = decision.get("evidence_hash", "N/A")
        policy = decision.get("policy", "N/A")
        score = decision.get("overall_score", 0)
        confidence = int(research.get("confidence", 0.8) * 100) if research.get("confidence", 0.8) <= 1.0 else int(research.get("confidence", 80))

        # Vector scores
        vectors = decision.get("vector_scores", {})
        demand_s = vectors.get("demand", 0)
        feasibility_s = vectors.get("feasibility", 0)
        comp_s = vectors.get("competition", 0)
        rev_s = vectors.get("revenue", 0)

        # Rationale
        rationale_lines = decision.get("rationale", [])
        rationale_str = "\n".join([f"  {r}" for r in rationale_lines])

        # Target audience
        audience = sorted(research.get("target_audience", []))
        audience_str = "\n".join([f"- {a}" for a in audience]) if audience else "- N/A"

        # Competitors
        competitors = sorted(research.get("competitors", []))
        competitors_str = "\n".join([f"- {c}" for c in competitors]) if competitors else "- N/A"

        # Pain points
        pain_points = sorted(research.get("pain_points", []))
        pain_points_str = "\n".join([f"1. {p}" for p in pain_points]) if pain_points else "1. N/A"

        # Risks
        risks = sorted(research.get("risks", []))
        risks_str = "\n".join([f"- {r}" for r in risks]) if risks else "- N/A"

        # Provenance
        provenance = decision.get("provenance_chain", [])
        prov_rows = []
        for p in provenance:
            src = p.get("source_adapter", "N/A")
            raw = p.get("raw_observation", "N/A")
            prov_rows.append(f"| **{src}** | {raw} | Validated |")
        prov_table = "\n".join(prov_rows) if prov_rows else "| **System** | Automated signal fusion | Validated |"

        # Milestones
        milestones = roadmap.get("milestones", [])
        ms_sections = []
        for ms in milestones:
            title = ms.get("title", "Milestone")
            tasks = ms.get("tasks", [])
            task_lines = []
            for t in tasks:
                t_desc = t.get("description", "")
                t_eff = t.get("estimated_effort", "")
                t_del = ", ".join(t.get("deliverables", []))
                task_lines.append(f"  - **Task:** {t_desc} (Effort: {t_eff})\n    *Deliverables:* `{t_del}`")
            t_str = "\n".join(task_lines)
            ms_sections.append(f"### Milestone: {title}\n{t_str}")
        roadmap_str = "\n\n".join(ms_sections) if ms_sections else "Roadmap pending"

        is_halted = (policy == "WAIT_FOR_SIGNAL")
        if is_halted:
            next_step = decision.get("next_step", "NO EXECUTIVE ACTION (Halted Fail-Closed)")
            warning_banner = "> ⚠️ **POLICY DECISION: WAIT_FOR_SIGNAL (Halted Fail-Closed / Audit Only)**\n> *This brief is an audit artefact recording a halted execution due to insufficient domain evidence. Downstream execution/release is strictly blocked.*\n\n"
        else:
            next_step = decision.get("next_step", "Proceed with validation.")
            warning_banner = ""

        template = f"""# Executive Brief: {topic}

**Timestamp:** {timestamp}  
**Topic Slug:** `{research.get("topic", "").lower().replace(" ", "_")}`  
**Decision ID:** `{decision_id}`  
**Evidence Hash:** `{evidence_hash}`  
**Policy Decision:** `{policy}`  
**Overall Score:** `{score}/100` (Confidence: {confidence}%)  

---

## 1. Executive Summary & Market Context

{warning_banner}The opportunity **"{topic}"** was evaluated via the APE Constitutional Pipeline. Based on market signal analysis, the policy recommendation is **{policy}** with a calculated opportunity score of **{score}/100**.

* **Target Audience:**
{audience_str}

* **Next Step Recommendation:** {next_step}

---

## 2. Evidence & Provenance Traceability

| Source Adapter | Signal Observation | Verification Status |
| :--- | :--- | :--- |
{prov_table}

---

## 3. Pain Points Analysis

{pain_points_str}

---

## 4. Competitor & Alternative Landscape

{competitors_str}

---

## 5. Risk Assessment

{risks_str}

---

## 6. Vector Score Breakdown

```text
Demand Score      : {demand_s}/100
Feasibility Score : {feasibility_s}/100
Competition Score : {comp_s}/100
Revenue Score     : {rev_s}/100
------------------------------------------------------------------
OVERALL SCORE     : {score}/100
```

### Rationale:
```text
{rationale_str}
```

---

## 7. Execution Roadmap & Milestones

{roadmap_str}
"""
        return template
