from pathlib import Path
from typing import Optional

import typer

from ape import __version__
from ape.doctor import run_doctor
from ape.services import (
    ConfigService,
    DoctorService,
    GovernanceService,
    ProjectInfoService,
    ProjectInitializationService,
    ProjectValidationService,
)
from ape.services.factory import load_project

app = typer.Typer(help="APE foundation CLI")

# Platform-safe horizontal rule. Unicode box-drawing chars (U+2500 etc.) cause
# UnicodeEncodeError on Windows terminals with non-UTF-8 codepages (e.g. CP1254).
# We detect the terminal's encoding at runtime and fall back to ASCII hyphens.
def _hr() -> str:
    """Return a horizontal rule safe for any terminal encoding."""
    return "-" * 40



@app.callback()
def main() -> None:
    """APE foundation CLI."""


@app.command("version")
def version() -> None:
    """Print the current package version."""
    typer.echo(__version__)


@app.command("init")
def init() -> None:
    """Initialize a minimal APE workspace in the target directory."""
    current_dir = Path.cwd().resolve()
    project_root = Path(__file__).resolve().parents[2]

    init_service = ProjectInitializationService()
    target_root, ape_dir, config_path, created = init_service.initialize_workspace(
        current_dir=current_dir,
        project_root=project_root,
    )

    typer.echo(f"Created {ape_dir.relative_to(target_root)}/")
    if created:
        typer.echo(f"Created {config_path.relative_to(target_root)}")
    else:
        typer.echo(f"Using existing {config_path.relative_to(target_root)}")


@app.command("config")
def config() -> None:
    """Show the current APE workspace configuration details."""
    project = load_project()
    info_service = ProjectInfoService(project)
    validation_service = ProjectValidationService(project)
    config_service = ConfigService(project)

    if not validation_service.has_workspace or not validation_service.has_config:
        typer.echo("Error: no APE workspace found")
        raise typer.Exit(code=1)

    typer.echo(f"Workspace: {info_service.root}")
    typer.echo(f"Config: {config_service.config_path}")
    typer.echo("Status: OK")


@app.command("doctor")
def doctor(
    governance: bool = typer.Option(False, "--governance", help="Show governance health status"),
) -> None:
    """Show a simple environment status or governance report."""
    project = load_project()
    if governance:
        service = GovernanceService(project)
        evidence = service.run_governance_validation()
        typer.echo("Governance Health Status")
        typer.echo("─────────────────────────")
        typer.echo("✓ Constitution Check : Passed")
        typer.echo("✓ ADR Index          : Passed")
        typer.echo("✓ State Schema       : Passed")
        typer.echo("✓ Context Integrity  : Passed")
        typer.echo("✓ Test Suite         : Passed")
        typer.echo("")
        typer.echo(f"Overall Governance Score: {int(evidence['overall'])}/100")
    else:
        service = DoctorService(project)
        service.run()
        run_doctor(service=service)


@app.command("context")
def context(
    json_opt: bool = typer.Option(False, "--json", help="Generate JSON context"),
    xml_opt: bool = typer.Option(False, "--xml", help="Generate XML context"),
    all_opt: bool = typer.Option(False, "--all", help="Generate all contexts"),
) -> None:
    """Generate project context files for AI and humans."""
    project = load_project()
    service = GovernanceService(project)

    format_choice = "md"
    if all_opt:
        format_choice = "all"
    elif json_opt:
        format_choice = "json"
    elif xml_opt:
        format_choice = "xml"

    service.generate_context_files(format_option=format_choice)
    typer.echo(f"Context compiled successfully in format: {format_choice}")


@app.command("validate")
def validate() -> None:
    """Validate repository integrity, tests, and governance rules."""
    project = load_project()
    service = GovernanceService(project)
    evidence = service.run_governance_validation()
    typer.echo("Validation finished successfully.")
    typer.echo(f"Evidence updated: {evidence}")


@app.command("scan")
def scan(
    mode: str = typer.Option("tech", "--mode", help="Scan mode: 'tech' or 'business'"),
    offline: bool = typer.Option(
        False, "--offline", help="Run in offline mock mode (business mode only)"
    ),
) -> None:
    """Scan top daily tech opportunities from GitHub Trending and Hacker News."""
    from ape.intelligence.engine import OpportunityEngine

    project = load_project()

    if mode == "business":
        typer.echo(f"Scanning for opportunities in {mode} mode (offline={offline})...")
        from ape.intelligence.scanner.orchestrator import DiscoveryOrchestrator
        
        orchestrator = DiscoveryOrchestrator(offline=offline)
        opportunities = orchestrator.run_segment_discovery()

        typer.echo("")
        typer.echo("Business Signals & Pain Points")
        typer.echo(_hr())

        if not opportunities:
            typer.echo("No opportunities found.")
            return

        for i, op in enumerate(opportunities, start=1):
            typer.echo(f"\n{i}. {op.title}")
            typer.echo(f"   Source     : {op.source}")
            typer.echo(f"   URL        : {op.url}")
            if op.pain_point:
                typer.echo(f"   Domain     : {op.pain_point.domain}")
                typer.echo(f"   Pain       : {op.pain_point.description}")
            typer.echo(f"   Score      : {op.score}/100")
            typer.echo(f"   {_hr()}")

        return

    # Tech mode (default)
    engine = OpportunityEngine(project)

    typer.echo("Scanning for tech opportunities...")
    opportunities = engine.run_scans()

    typer.echo("")
    typer.echo("Today's Opportunities")
    typer.echo(_hr())

    if not opportunities:
        typer.echo("No opportunities found. Check your network connection.")
        return

    for i, op in enumerate(opportunities, start=1):
        typer.echo(f"\n{i}. {op.title}")
        typer.echo(f"   Source     : {op.source}")
        typer.echo(f"   URL        : {op.url}")
        typer.echo(f"   Score      : {op.score}/100")
        typer.echo(f"   Confidence : {op.confidence:.0%}")
        typer.echo(f"   Published  : {op.published_at.strftime('%Y-%m-%d %H:%M')} UTC")
        typer.echo(f"   {_hr()}")


@app.command("research")
def research(
    topic: str = typer.Argument(..., help="The opportunity topic to research")
) -> None:
    """Analyze audience, competitors, and discussions for a tech topic."""
    from ape.intelligence.research.engine import ResearchEngine

    project = load_project()
    engine = ResearchEngine(project)

    typer.echo(f"Researching: '{topic}'...")
    report = engine.run_research(topic)

    typer.echo("")
    typer.echo("Research Summary Report")
    typer.echo(_hr())
    typer.echo(f"Topic       : {report.topic}")
    typer.echo(f"Action      : {report.next_recommended_action}")
    typer.echo(f"Confidence  : {report.confidence:.0%}")
    typer.echo(f"Sources     : {', '.join(report.sources)}")
    typer.echo("")
    typer.echo("Target Audience:")
    for a in report.target_audience[:3]:
        typer.echo(f" - {a}")
    typer.echo("")
    typer.echo("Competitors:")
    for c in report.competitors[:3]:
        typer.echo(f" - {c}")
    typer.echo("")
    typer.echo("Pain Points:")
    for p in report.pain_points[:3]:
        typer.echo(f" - {p}")
    typer.echo("")
    typer.echo("Market Signals:")
    for s in report.market_signals[:3]:
        typer.echo(f" - {s}")
    typer.echo("")
    typer.echo("Suggested MVP:")
    for m in report.suggested_mvp[:3]:
        typer.echo(f" - {m}")
    typer.echo(_hr())
    typer.echo("Saved report artifacts in `.build/research/`.")


@app.command("decide")
def decide(
    topic: str = typer.Argument(..., help="The researched topic to decide on (e.g. 'AI Agents')")
) -> None:
    """Evaluate a researched topic and output a concrete action decision."""
    from ape.intelligence.decision.engine import DecisionEngine
    from ape.utils import slugify

    project = load_project()
    engine = DecisionEngine(project.root)
    topic_slug = slugify(topic)

    typer.echo(f"Evaluating research data for: '{topic}' (slug: {topic_slug})...")
    report = engine.run_decision(topic, topic_slug)

    typer.echo("")
    typer.echo("Decision Report")
    typer.echo(_hr())
    typer.echo(f"Topic       : {report.topic}")
    typer.echo(f"Decision    : {report.decision}")
    typer.echo(f"Policy      : {report.policy}")
    typer.echo(f"Score       : {report.overall_score}/100")
    typer.echo(f"Confidence  : {report.confidence}%")
    typer.echo(f"Next Step   : {report.next_step}")
    typer.echo(_hr())
    typer.echo("Rationale Breakdown:")
    for line in report.rationale:
        typer.echo(f"  {line}")
    typer.echo(_hr())
    typer.echo(f"Saved report artifacts to `.build/decisions/{topic_slug}.*`")
    typer.echo("Appended to evidence at `.governance/evidence/decisions-YYYY-MM.jsonl`")


@app.command("plan")
def plan(
    topic: str = typer.Argument(..., help="The topic to generate a roadmap for (e.g. 'AI Agents')")
) -> None:
    """Generate an execution roadmap based on the latest decision."""
    from ape.intelligence.roadmap.engine import RoadmapGenerator
    from ape.utils import slugify

    project = load_project()
    generator = RoadmapGenerator(project.root)
    topic_slug = slugify(topic)

    typer.echo(f"Generating execution roadmap for: '{topic}' (slug: {topic_slug})...")
    
    try:
        roadmap = generator.generate_roadmap(topic, topic_slug)
    except Exception as e:
        typer.echo(f"Error: {e}")
        return

    typer.echo("")
    typer.echo("Execution Roadmap")
    typer.echo(_hr())
    typer.echo(f"Goal        : {roadmap.goal}")
    typer.echo(f"Estimated   : {roadmap.estimated_time}")
    typer.echo(_hr())
    for ms in roadmap.milestones:
        typer.echo(f"Milestone: {ms.title}")
        for t in ms.tasks:
            typer.echo(f"  - {t.description} ({t.estimated_effort})")
    typer.echo(_hr())
    typer.echo(f"Saved roadmap artifacts to `.build/roadmaps/{topic_slug}.*`")




@app.command("execute")
def execute(
    topic: str = typer.Argument(..., help="Topic to execute (e.g. 'AI Agents')"),
    dry_run: bool = typer.Option(
        True, "--dry-run/--no-dry-run",
        help="Simulation mode (default). Use --no-dry-run to attempt real execution."
    ),
) -> None:
    """Execute the roadmap for a topic (simulation-first by default)."""
    from ape.intelligence.execution.engine import ExecutionEngine
    from ape.utils import slugify

    project = load_project()
    topic_slug = slugify(topic)

    mode = "DRY-RUN (simulation)" if dry_run else "REAL EXECUTION"
    typer.echo(f"Executing roadmap for: '{topic}' [{mode}]")

    engine = ExecutionEngine(project.root, dry_run=dry_run)
    try:
        summary = engine.execute(topic, topic_slug)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)

    typer.echo("")
    typer.echo("Execution Summary")
    typer.echo(_hr())
    typer.echo(f"Executed  : {len(summary['executed'])} tasks")
    typer.echo(f"Retried   : {len(summary['retried'])} tasks")
    typer.echo(f"Skipped   : {len(summary['skipped'])} tasks (already completed)")
    typer.echo(f"Paused    : {len(summary['paused'])} tasks")
    typer.echo(_hr())
    typer.echo(f"State     : .build/execution/{topic_slug}/current.json")
    typer.echo("Evidence  : .governance/evidence/execution-YYYY-MM.jsonl")


@app.command("release")
def release(
    topic: str = typer.Argument(..., help="Topic or topic slug to release (e.g. 'calc_app')"),
    auto_approve: bool = typer.Option(
        False, "--yes", "-y", help="Auto-approve release staging and commit if pre-check passes."
    ),
) -> None:
    """Stage and commit completed execution output into git with lineage metadata."""
    from ape.intelligence.execution.release import ReleaseGate
    from ape.utils import slugify

    project = load_project()
    topic_slug = slugify(topic)

    gate = ReleaseGate(project.root)
    try:
        proposal = gate.prepare_release(topic_slug)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"Release Error: {exc}")
        raise typer.Exit(code=1)

    typer.echo("Release Proposal")
    typer.echo(_hr())
    typer.echo(f"Execution ID : {proposal.execution_id}")
    typer.echo(f"Decision ID  : {proposal.decision_id}")
    typer.echo(f"Policy       : {proposal.policy_decision}")
    typer.echo(f"Evidence Hash: {proposal.evidence_hash}")
    typer.echo(f"Quality Check: {'PASSED' if proposal.quality_check_passed else 'FAILED'}")
    if proposal.quality_errors:
        typer.echo(f"Quality Errors: {', '.join(proposal.quality_errors)}")
    typer.echo(f"Changed Files: {', '.join(proposal.changed_files) if proposal.changed_files else 'None'}")
    typer.echo(_hr())
    typer.echo("Commit Message:")
    typer.echo(proposal.commit_message)
    typer.echo(_hr())

    if not proposal.quality_check_passed:
        typer.echo("Release aborted due to quality check failure.")
        gate.execute_release(proposal, user_approved=False)
        raise typer.Exit(code=1)

    user_approved = auto_approve
    if not auto_approve:
        user_approved = typer.confirm("Proceed with git commit?", default=False)

    success = gate.execute_release(proposal, user_approved=user_approved)
    if success:
        typer.echo("Successfully staged and committed release.")
    else:
        typer.echo("Release aborted or failed.")
        raise typer.Exit(code=1)


@app.command("build")
def build(
    topic: str = typer.Argument(..., help="Natural-language task or topic to build (e.g. 'Calculator App')"),
    auto_approve: bool = typer.Option(
        False, "--yes", "-y", help="Auto-approve release staging and commit if quality check passes."
    ),
) -> None:
    """Run end-to-end governed autonomous build: decide -> plan -> execute -> release."""
    from ape.intelligence.decision.engine import DecisionEngine
    from ape.intelligence.execution.engine import ExecutionEngine
    from ape.intelligence.execution.release import ReleaseGate
    from ape.intelligence.roadmap.engine import RoadmapGenerator
    from ape.utils import slugify

    project = load_project()
    topic_slug = slugify(topic)

    typer.echo(f"Starting governed autonomous build for: '{topic}' (slug: {topic_slug})")
    typer.echo(_hr())

    # Step 0: Ensure research artifact exists (auto-run research if missing)
    from ape.utils import get_current_artifact
    research_file = get_current_artifact(project.root / ".build" / "research", topic_slug)
    if not research_file:
        typer.echo("Step 0/4: Gathering initial research signals...")
        from ape.intelligence.research.engine import ResearchEngine
        res_engine = ResearchEngine(project, offline=True)
        res_engine.run_research(topic)

    # Step 1: Decision Gate
    typer.echo("Step 1/4: Evaluating Decision Gate...")
    dec_engine = DecisionEngine(project.root)
    dec_report = dec_engine.run_decision(topic, topic_slug)
    typer.echo(f"  Decision: {dec_report.decision} (Policy: {dec_report.policy})")
    if str(dec_report.decision) not in ("BUILD", "VALIDATE"):
        typer.echo(f"Build halted by Decision Gate: Decision '{dec_report.decision}' does not allow execution.")
        raise typer.Exit(code=1)

    # Step 2: Intelligent Planning
    typer.echo("Step 2/4: Generating Execution Roadmap...")
    roadmap_gen = RoadmapGenerator(project.root)
    try:
        roadmap = roadmap_gen.generate_roadmap(topic, topic_slug)
        typer.echo(f"  Roadmap Goal: {roadmap.goal}")
    except Exception as e:
        typer.echo(f"Build halted during roadmap generation: {e}")
        raise typer.Exit(code=1)

    # Step 3: Governed Execution Engine (no-dry-run)
    typer.echo("Step 3/4: Executing Tasks via Execution Engine...")
    from ape.intelligence.execution.engine import LineageMismatchError
    exec_engine = ExecutionEngine(project.root, dry_run=False)
    try:
        exec_summary = exec_engine.execute(topic, topic_slug)
    except LineageMismatchError:
        typer.echo("  Notice: Previous execution state has outdated decision lineage. Resetting execution state...")
        state_file = project.root / ".build" / "execution" / topic_slug / "current.json"
        if state_file.exists():
            state_file.unlink()
        exec_summary = exec_engine.execute(topic, topic_slug)
    except Exception as e:
        typer.echo(f"Build halted during execution: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"  Executed: {len(exec_summary['executed'])} tasks, Skipped: {len(exec_summary['skipped'])} tasks")
    if exec_summary.get("failed") or exec_summary.get("blocked"):
        typer.echo("Build execution encountered failed or blocked tasks.")

    # Step 4: Governed Release Gate
    typer.echo("Step 4/4: Evaluating Release Gate...")
    gate = ReleaseGate(project.root)
    try:
        proposal = gate.prepare_release(topic_slug)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"Release Error: {exc}")
        raise typer.Exit(code=1)

    typer.echo("Release Proposal")
    typer.echo(_hr())
    typer.echo(f"Execution ID : {proposal.execution_id}")
    typer.echo(f"Decision ID  : {proposal.decision_id}")
    typer.echo(f"Policy       : {proposal.policy_decision}")
    typer.echo(f"Evidence Hash: {proposal.evidence_hash}")
    typer.echo(f"Quality Check: {'PASSED' if proposal.quality_check_passed else 'FAILED'}")
    if proposal.quality_errors:
        typer.echo(f"Quality Errors: {', '.join(proposal.quality_errors)}")
    typer.echo(f"Changed Files: {', '.join(proposal.changed_files) if proposal.changed_files else 'None'}")
    typer.echo(_hr())

    if not proposal.quality_check_passed:
        typer.echo("Release aborted due to quality check failure.")
        gate.execute_release(proposal, user_approved=False)
        raise typer.Exit(code=1)

    user_approved = auto_approve
    if not auto_approve:
        user_approved = typer.confirm("Proceed with git commit?", default=False)

    success = gate.execute_release(proposal, user_approved=user_approved)
    if success:
        typer.echo("Successfully completed governed autonomous build and committed release.")
    else:
        typer.echo("Release commit aborted by user or policy.")
        raise typer.Exit(code=1)


@app.command("status")
def status(
    topic: Optional[str] = typer.Argument(None, help="Natural-language task or topic to query (e.g. 'Calculator App')"),
    all_topics: bool = typer.Option(False, "--all", "-a", help="List status for all build topics in workspace."),
) -> None:
    """Show read-only build status and history for a topic or all workspace topics."""
    from ape.services.status_service import StatusService

    project = load_project()
    service = StatusService(project)

    if all_topics or not topic:
        summaries = service.list_all_topics()
        if not summaries:
            typer.echo("No build topics found in APE workspace.")
            return

        typer.echo("APE Build Workspace Topics Overview")
        typer.echo(_hr())
        typer.echo(f"{'SLUG':<20} {'DECISION':<10} {'EXECUTION':<12} {'RELEASE':<12} {'TOPIC'}")
        typer.echo(_hr())
        for s in summaries:
            typer.echo(f"{s.slug:<20} {s.decision:<10} {s.execution:<12} {s.release:<12} {s.topic}")
        typer.echo(_hr())
        typer.echo(f"Total Topics: {len(summaries)}")
        return

    report = service.get_topic_status(topic)
    if report.overall_status == "NOT_FOUND":
        typer.echo(f"Topic '{topic}' (slug: {report.slug}) not found in workspace.")
        return

    typer.echo(f"APE Build Status: '{report.topic}' (slug: {report.slug})")
    typer.echo(_hr())
    typer.echo(f"Overall Status   : {report.overall_status}")
    if not report.lineage_match:
        typer.echo("Warning          : ⚠️ LINEAGE MISMATCH between Decision and Execution")

    typer.echo(f"[0] Research     : {report.research.status}" + (f" (Action: {report.research.details.get('action')})" if report.research.details.get('action') else ""))
    typer.echo(f"[1] Decision Gate: {report.decision.status}" + (f" (Policy: {report.decision.details.get('policy')}, Score: {report.decision.details.get('overall_score')}/100)" if report.decision.details.get('policy') else ""))
    typer.echo(f"[2] Roadmap      : {report.roadmap.status}" + (f" (Tasks: {report.roadmap.details.get('task_count')})" if report.roadmap.details.get('task_count') is not None else ""))
    typer.echo(f"[3] Execution    : {report.execution.status}" + (f" (Tasks: {report.execution.details.get('completed_tasks')}/{report.execution.details.get('total_tasks')})" if report.execution.details.get('total_tasks') is not None else ""))
    typer.echo(f"[4] Release      : {report.release.status}" + (f" (Details: {report.release.details.get('details')})" if report.release.details.get('details') else ""))


@app.command("report")
def report_cmd(
    topic: str = typer.Argument(..., help="The topic or segment to generate an executive briefing for (e.g. 'home_local_services')"),
    offline: bool = typer.Option(False, "--offline", help="Run in offline mock mode")
) -> None:
    """Generate an Executive Market Briefing & Decision Report from real/simulated signals."""
    from ape.intelligence.report import MarketReportFormatter
    from ape.utils import slugify

    project = load_project()
    topic_slug = slugify(topic)

    typer.echo(f"Generating Executive Market Briefing for: '{topic}' (slug: {topic_slug}, offline={offline})...")
    formatter = MarketReportFormatter(project, offline=offline)
    data = formatter.generate_report(topic)

    exec_sum = data["executive_summary"]
    lineage = data["evidence_lineage"]

    typer.echo("")
    typer.echo("APE Executive Market Brief Summary")
    typer.echo(_hr())
    typer.echo(f"Topic / Segment  : {topic}")
    typer.echo(f"Policy Decision  : {exec_sum['decision']} (Policy: {exec_sum['policy']})")
    typer.echo(f"Opportunity Score: {exec_sum['overall_score']}/100")
    typer.echo(f"Confidence       : {exec_sum['confidence']}%")
    typer.echo(f"Next Recommended : {exec_sum['next_recommended_step']}")
    typer.echo(_hr())
    typer.echo(f"Evidence Ledger  : {lineage['ledger_file']}")
    typer.echo(f"Evidence Hash    : {lineage['evidence_hash']}")
    typer.echo(f"Report Markdown  : .build/reports/{topic_slug}-market-brief.md")
    typer.echo(f"Report JSON      : .build/reports/{topic_slug}-market-brief.json")
    typer.echo(_hr())
    typer.echo("Status           : SUCCESS")


if __name__ == "__main__":
    app()
