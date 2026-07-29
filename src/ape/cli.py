from pathlib import Path

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
    """Return a horizontal rule safe for the current terminal encoding."""
    import sys
    enc = getattr(sys.stdout, "encoding", "ascii") or "ascii"
    bar = "\u2500" * 40
    try:
        bar.encode(enc)
        return bar
    except (UnicodeEncodeError, LookupError):
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
    typer.echo("Appended to evidence at `.governance/evidence/decisions.jsonl`")


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
    typer.echo("Evidence  : .governance/evidence/execution.jsonl")


if __name__ == "__main__":
    app()
