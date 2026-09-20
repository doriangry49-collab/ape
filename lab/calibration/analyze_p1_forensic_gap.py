"""P1.3 Forensic Gap Analysis — Read-Only Evidence-to-Decision Chain Trace.

No code changes. No scorer changes. No G3b modifications.
Traces ev_p1_001..004 through every mapping step to produce
a per-step PRESENT / MISSING / INCONSISTENT / UNVERIFIABLE audit.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from ape.intelligence.ablation.representation_contract import sanitize_snapshot_input
from lab.calibration.run_g3b3c_ablation import build_r1_scorer_input

PAIN_KWS = ("pain", "problem", "struggling", "issue", "bottleneck", "frustrated")
DISC_KWS = ("discussion", "comments", "debate", "thread", "forum", "community")
HW_KWS   = ("hardware", "robot", "sensor", "device", "iot")

raw_evidence = [
    {
        "snapshot_id": "ev_p1_001",
        "source": "github_discussions",
        "source_type": "developer_forum",
        "observed_at": "2026-08-15T14:22:10Z",
        "raw_observation": "High CPU and memory footprint of Grafana Loki and Fluentbit on low-resource IoT gateway devices created severe bottleneck and disk space exhaustion issues.",
        "relevance_score": 0.92,
    },
    {
        "snapshot_id": "ev_p1_002",
        "source": "hackernews_thread",
        "source_type": "community_debate",
        "observed_at": "2026-08-18T09:11:45Z",
        "raw_observation": "Developers struggling with expensive cloud observability bills (Datadog/Honeycomb) for edge Kubernetes clusters, seeking lightweight self-hosted alternative.",
        "relevance_score": 0.88,
    },
    {
        "snapshot_id": "ev_p1_003",
        "source": "arxiv_preprints",
        "source_type": "technical_paper",
        "observed_at": "2026-08-20T11:00:00Z",
        "raw_observation": "Embedded ClickHouse and Vector pipeline benchmarks show 85% compression ratio and sub-10ms query latency on ARM64 single-board computers.",
        "relevance_score": 0.95,
    },
    {
        "snapshot_id": "ev_p1_004",
        "source": "reddit_devops",
        "source_type": "user_feedback",
        "observed_at": "2026-08-25T18:40:12Z",
        "raw_observation": "Frequent network disconnections on industrial edge gateways require robust local buffering and store-and-forward log aggregation features.",
        "relevance_score": 0.85,
    },
]

record = {
    "opportunity_id": "opp_p1_edge_analytics_001",
    "prompt_topic": "Self-Hosted Open-Source Infrastructure & Log Analytics Platform for Edge Deployments",
    "evidence_snapshots": raw_evidence,
}

topic = record["prompt_topic"].lower()

print("=" * 70)
print("P1.3 — FORENSIC EVIDENCE-TO-DECISION GAP ANALYSIS")
print("Mode: READ-ONLY. No code changes. No scorer changes.")
print("=" * 70)
print()

# ── Step 1: EV → KEYWORD MAPPING TRACE ──────────────────────────────────────
print("STEP 1: Raw Observation → Keyword Match Trace")
print("-" * 70)

ev_trace = []
for ev in raw_evidence:
    obs = ev["raw_observation"].lower()
    pain_hits = [kw for kw in PAIN_KWS if kw in obs]
    disc_hits  = [kw for kw in DISC_KWS  if kw in obs]
    is_pain = len(pain_hits) > 0
    is_disc = len(disc_hits) > 0
    ev_trace.append({
        "snapshot_id": ev["snapshot_id"],
        "source": ev["source"],
        "pain_kws_matched": pain_hits,
        "disc_kws_matched": disc_hits,
        "contributes_pain_point": is_pain,
        "contributes_discussion": is_disc,
        "relevance_score": ev["relevance_score"],
    })
    print(f"  {ev['snapshot_id']} [{ev['source']}]")
    print(f"    obs:        {ev['raw_observation'][:90]}...")
    print(f"    pain kws:   {pain_hits}  → contributes_pain_point: {is_pain}")
    print(f"    disc kws:   {disc_hits}  → contributes_discussion: {is_disc}")
    print()

# ── Step 2: TOPIC → HARDWARE FLAG ───────────────────────────────────────────
hw_hits = [kw for kw in HW_KWS if kw in topic]
is_hardware = len(hw_hits) > 0
risks = ["r1", "r2", "r3"] if is_hardware else ["r1", "r2"]

print("STEP 2: Topic → Hardware Flag")
print("-" * 70)
print(f"  topic:       {record['prompt_topic'][:70]}")
print(f"  hw_kws:      {hw_hits}  → is_hardware: {is_hardware}")
print(f"  risks:       {risks}")
print()

# ── Step 3: SCORER INPUT ASSEMBLY ───────────────────────────────────────────
scorer_input = build_r1_scorer_input(sanitize_snapshot_input(record))

pain_count = len(scorer_input["pain_points"])
disc_count  = len(scorer_input["discussions"])
risk_count  = len(scorer_input["risks"])
comp_count  = len(scorer_input["competitors"])
aud_count   = len(scorer_input["target_audience"])

print("STEP 3: Scorer v1 Input Assembly")
print("-" * 70)
print(f"  pain_points:     {scorer_input['pain_points']}   (count={pain_count})")
print(f"  discussions:     {scorer_input['discussions']}    (count={disc_count})")
print(f"  risks:           {scorer_input['risks']}  (count={risk_count})")
print(f"  competitors:     {scorer_input['competitors']}    (count={comp_count})")
print(f"  target_audience: {scorer_input['target_audience']}  (count={aud_count})")
print()

# ── Step 4: CONFIDENCE DERIVATION ───────────────────────────────────────────
avg_rel = sum(ev["relevance_score"] for ev in raw_evidence) / len(raw_evidence)
confidence_score = round(avg_rel * 100, 1)

print("STEP 4: Confidence Score Derivation")
print("-" * 70)
print("  formula: avg(relevance_scores) * 100")
print(f"  relevance_scores: {[ev['relevance_score'] for ev in raw_evidence]}")
print(f"  avg_relevance:    {round(avg_rel, 4)}")
print(f"  confidence_score: {confidence_score}")
print()

# ── Step 5: DEFECT INVENTORY ─────────────────────────────────────────────────
print("=" * 70)
print("STEP 5: DEFECT INVENTORY (P1-D01 through P1-D09)")
print("=" * 70)
print()

defects = [
    {
        "id": "P1-D01",
        "severity": "RED",
        "title": "Evidence → Demand Mapping: PARTIALLY PRESENT but BROKEN",
        "finding": f"ev_p1_001 matched pain kws ['bottleneck','issue'] → contributes pain_point. "
                   f"ev_p1_002 matched ['struggling'] → contributes pain_point. "
                   f"Final pain_count={pain_count}. "
                   f"BUT ev_p1_002 ('seeking lightweight self-hosted alternative') and ev_p1_004 ('store-and-forward demand') "
                   f"carry STRONG demand signal yet they hit disc_kws=[] → discussions=0. "
                   f"The discussion/debate signal from hackernews_thread (community_debate type) is LOST "
                   f"because 'debate'/'community' do not appear verbatim in the raw_observation text. "
                   f"disc_count=0 → Demand contribution from discussions: 0.",
        "verdict": "MISSING — disc_count=0 despite 2 community-type sources",
    },
    {
        "id": "P1-D02",
        "severity": "RED",
        "title": "Evidence → Feasibility Mapping: OPAQUE / UNVERIFIABLE",
        "finding": f"Scorer v1 derived Feasibility from risk_count={risk_count} (risks={risks}). "
                   f"These risks are HARDCODED in build_r1_scorer_input: "
                   f"is_hardware={is_hardware} → risks=['r1','r2']. "
                   f"'r1' and 'r2' are placeholder tokens — no mapping to ev_p1_001/002/003/004 exists. "
                   f"ev_p1_003 (arXiv benchmark: 85%% compression, sub-10ms latency) is the only feasibility "
                   f"evidence in the ledger, but it contributes NOTHING to risks[] or Feasibility. "
                   f"Feasibility=70 is produced entirely from a topic-keyword flag, not from evidence content.",
        "verdict": "UNVERIFIABLE — Feasibility score not derived from collected evidence",
    },
    {
        "id": "P1-D03",
        "severity": "RED",
        "title": "Evidence → Competition Mapping: HARDCODED / MISSING",
        "finding": f"competitors={scorer_input['competitors']} is a static hardcoded placeholder ['c1']. "
                   f"No evidence snapshot identifies a competitor by name. "
                   f"ev_p1_002 mentions Datadog/Honeycomb — these are real named competitors — "
                   f"but they are not extracted into the competitors list. "
                   f"Competition=80 reflects a default single-competitor penalty, not observed market data.",
        "verdict": "MISSING — Named competitors in evidence not mapped; hardcoded placeholder used",
    },
    {
        "id": "P1-D04",
        "severity": "RED",
        "title": "Evidence → Revenue Mapping: HARDCODED / MISSING",
        "finding": f"target_audience={scorer_input['target_audience']} = ['seg1','seg2'] — static placeholders. "
                   f"No evidence snapshot identifies a target audience segment. "
                   f"Revenue=60 reflects a default two-segment configuration, not observed willingness-to-pay signals.",
        "verdict": "MISSING — Target audiences not derived from evidence; Revenue is evidence-free",
    },
    {
        "id": "P1-D05",
        "severity": "RED",
        "title": "Confidence 90.0% — Formula Exposed but Epistemically Invalid",
        "finding": f"confidence_score = avg(relevance_scores) * 100 = {confidence_score}. "
                   f"relevance_scores are SELF-ASSIGNED static floats embedded in the raw_evidence list "
                   f"at time of evidence collection, not computed by any independent quality metric. "
                   f"The formula does not account for: source independence, claim coverage, contradiction rate, "
                   f"recency weighting, or evidence completeness vs. scorer dimensions. "
                   f"90%% confidence claims 'Yuksek Kanit Otoritesi' but the formula proves this is "
                   f"avg(self-reported relevance) only.",
        "verdict": "UNVERIFIABLE — Confidence = avg of hardcoded self-assigned relevance scores",
    },
    {
        "id": "P1-D06",
        "severity": "ORANGE",
        "title": "4 'Independent' Sources — Epistemic Independence Not Established",
        "finding": "github_discussions, hackernews_thread, arxiv_preprints, reddit_devops are 4 different "
                   "channels but could reference the same root problem report. No deduplication or "
                   "cross-reference check was performed. Independence is asserted, not verified.",
        "verdict": "UNVERIFIABLE — Independence of sources not tested",
    },
    {
        "id": "P1-D07",
        "severity": "ORANGE",
        "title": "Section 4 Labelled 'Human Expert Review' — Actually System-Generated",
        "finding": "The brief's Section 4 ('Human Expert Review & Actionable Next Steps') contains "
                   "only system-generated rationale text. No human expert reviewed this document. "
                   "The label is misleading. Correct label should be 'System Rationale / Awaiting Human Review'.",
        "verdict": "INCONSISTENT — Label claims human review; content is system-generated",
    },
    {
        "id": "P1-D08",
        "severity": "ORANGE",
        "title": "Market Conclusion Overstated — 'net kanıtlar sunmaktadır'",
        "finding": "Brief concludes 'self-hosted bir cozum icin net kanitlar sunmaktadir'. "
                   "Four observations showing operational pain and cost sensitivity do not constitute "
                   "validated market opportunity evidence. Correct claim: 'dogrulanmasi gereken sinyaller mevcuttur'.",
        "verdict": "INCONSISTENT — Conclusion overstates evidential strength",
    },
    {
        "id": "P1-D09",
        "severity": "ORANGE",
        "title": "Actionable Next Steps Absent",
        "finding": "Section 4 contains no concrete next validation steps (e.g., customer interview target, "
                   "competitor pricing research, prototype feasibility check). A decision-maker reading this "
                   "brief cannot determine what to do next from the artifact alone.",
        "verdict": "MISSING — No actionable validation roadmap",
    },
]

for d in defects:
    sev_icon = "🔴" if d["severity"] == "RED" else "🟠"
    print(f"{sev_icon} {d['id']}  [{d['severity']}]  {d['title']}")
    print(f"   Finding: {d['finding'][:200]}...")
    print(f"   Verdict: {d['verdict']}")
    print()

# ── Step 6: SUMMARY TABLE ────────────────────────────────────────────────────
print("=" * 70)
print("FORENSIC SUMMARY TABLE")
print("=" * 70)
rows = [
    ("RAW OBSERVATION → PAIN POINT", "ev_p1_001,002", "PRESENT (kw match)", "PRESENT"),
    ("RAW OBSERVATION → DISCUSSION", "ev_p1_002,004", "DISC KW NOT IN TEXT", "MISSING"),
    ("RAW OBSERVATION → FEASIBILITY", "ev_p1_003", "NOT USED IN MAPPING", "MISSING"),
    ("RAW OBSERVATION → COMPETITOR", "ev_p1_002 (Datadog)", "NOT EXTRACTED", "MISSING"),
    ("RAW OBSERVATION → AUDIENCE", "(none)", "HARDCODED PLACEHOLDER", "MISSING"),
    ("CONFIDENCE DERIVATION", "avg(self-reported rel)", "NOT INDEPENDENT", "UNVERIFIABLE"),
    ("SOURCE INDEPENDENCE", "4 sources", "NOT TESTED", "UNVERIFIABLE"),
    ("HUMAN REVIEW LABEL", "Section 4", "SYSTEM GENERATED", "INCONSISTENT"),
    ("MARKET CONCLUSION", "Brief closing", "OVERSTATED", "INCONSISTENT"),
    ("ACTIONABLE NEXT STEPS", "Section 4", "ABSENT", "MISSING"),
]
print(f"  {'Chain Step':<35} {'Evidence':<22} {'Status Detail':<25} {'Verdict'}")
print("  " + "-" * 100)
for row in rows:
    print(f"  {row[0]:<35} {row[1]:<22} {row[2]:<25} {row[3]}")

print()
print("=" * 70)
print("P1.3 FORENSIC GAP ANALYSIS COMPLETE — READ-ONLY PASS")
print("G3b: UNCHANGED | Scorer v1: UNCHANGED | Datasets: UNCHANGED")
print("=" * 70)

# Write structured output
output = {
    "analysis": "P1.3 Evidence-to-Decision Forensic Gap Analysis",
    "mode": "READ-ONLY",
    "ev_trace": ev_trace,
    "hardware_flag": {"is_hardware": is_hardware, "hw_kws_matched": hw_hits},
    "scorer_input_actual": scorer_input,
    "confidence_derivation": {
        "formula": "avg(relevance_scores) * 100",
        "relevance_scores": [ev["relevance_score"] for ev in raw_evidence],
        "avg_relevance": round(avg_rel, 4),
        "confidence_score": confidence_score,
    },
    "defects": defects,
}

out_path = REPO_ROOT / ".governance" / "evidence" / "p1_forensic_gap_analysis.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\nForensic analysis evidence written (READ-ONLY): {out_path}")
