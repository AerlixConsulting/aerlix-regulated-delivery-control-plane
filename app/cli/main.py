"""Aerlix CLI — regulated delivery control plane command-line interface.

Usage:
    aerlix [command] [options]

Commands:
    init-demo               Seed the database with demo data
    ingest-requirements     Load requirements from a YAML file
    ingest-controls         Load controls from a YAML file
    ingest-evidence         Load evidence items from a JSON file
    ingest-sbom             Ingest an SBOM file for an artifact
    evaluate-release        Run policy evaluation for a release
    generate-audit-bundle   Generate an audit bundle
    trace show              Show traceability for a requirement or control
    graph export            Export the full traceability graph
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="aerlix",
    help="🛡️  Aerlix Regulated Delivery Control Plane CLI",
    add_completion=False,
    rich_markup_mode="rich",
)

trace_app = typer.Typer(name="trace", help="Traceability commands")
app.add_typer(trace_app, name="trace")

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine from sync context."""
    return asyncio.run(coro)


def _get_db_session():  # type: ignore[no-untyped-def]
    """Return a synchronous-wrapped async DB session context manager."""
    from app.db import AsyncSessionLocal

    return AsyncSessionLocal()


# ---------------------------------------------------------------------------
# init-demo
# ---------------------------------------------------------------------------


@app.command("init-demo")
def init_demo(
    force: bool = typer.Option(False, "--force", help="Drop and recreate tables"),
) -> None:
    """🎬 Seed the database with demo data for the regulated payments API scenario."""
    console.print(Panel("[bold cyan]Aerlix Control Plane — Demo Init[/bold cyan]"))

    try:
        import sample_data.seed_db as seeder

        _run(seeder.seed(force=force))
        console.print("✅ [green]Demo database seeded successfully.[/green]")
        console.print(
            "\n[bold]Next steps:[/bold]\n"
            "  • Visit the API docs: [blue]http://localhost:8000/docs[/blue]\n"
            "  • Visit the dashboard: [blue]http://localhost:3000[/blue]\n"
        )
    except Exception as exc:
        console.print(f"[red]Error seeding database:[/red] {exc}")
        raise typer.Exit(code=1) from exc


# ---------------------------------------------------------------------------
# ingest-requirements
# ---------------------------------------------------------------------------


@app.command("ingest-requirements")
def ingest_requirements(
    path: Path = typer.Argument(..., help="Path to requirements YAML file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Parse only, do not write to DB"),
) -> None:
    """📋 Ingest requirements from a YAML file into the control plane."""
    if not path.exists():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(code=1)

    with path.open() as f:
        data = yaml.safe_load(f)

    reqs = data.get("requirements", [])
    console.print(f"[cyan]Found {len(reqs)} requirements in {path}[/cyan]")

    if dry_run:
        table = Table("req_id", "title", "type", "status")
        for r in reqs:
            table.add_row(
                r.get("req_id", ""), r.get("title", ""), r.get("type", ""), r.get("status", "")
            )
        console.print(table)
        return

    async def _ingest():
        from sqlalchemy import select

        from app.db import AsyncSessionLocal
        from app.models import Requirement

        async with AsyncSessionLocal() as db:
            created = 0
            skipped = 0
            for r in reqs:
                existing = await db.execute(
                    select(Requirement).where(Requirement.req_id == r["req_id"])
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue
                req = Requirement(
                    req_id=r["req_id"],
                    title=r["title"],
                    description=r.get("description"),
                    req_type=r.get("type", "system"),
                    status=r.get("status", "draft"),
                    priority=r.get("priority"),
                    source=r.get("source"),
                )
                db.add(req)
                created += 1
            await db.commit()
            return created, skipped

    created, skipped = _run(_ingest())
    console.print(
        f"✅ [green]Ingested {created} requirements[/green] ({skipped} skipped — already exist)"
    )


# ---------------------------------------------------------------------------
# ingest-controls
# ---------------------------------------------------------------------------


@app.command("ingest-controls")
def ingest_controls(
    path: Path = typer.Argument(..., help="Path to controls YAML file"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """🔒 Ingest NIST-aligned controls from a YAML file."""
    if not path.exists():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(code=1)

    with path.open() as f:
        data = yaml.safe_load(f)

    controls = data.get("controls", [])
    console.print(f"[cyan]Found {len(controls)} controls in {path}[/cyan]")

    if dry_run:
        table = Table("control_id", "family", "title", "baseline")
        for c in controls:
            table.add_row(
                c.get("control_id", ""),
                c.get("family", ""),
                c.get("title", "")[:60],
                c.get("baseline", ""),
            )
        console.print(table)
        return

    async def _ingest():
        from sqlalchemy import select

        from app.db import AsyncSessionLocal
        from app.models import Control

        async with AsyncSessionLocal() as db:
            created = 0
            skipped = 0
            for c in controls:
                existing = await db.execute(
                    select(Control).where(Control.control_id == c["control_id"])
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue
                ctrl = Control(
                    control_id=c["control_id"],
                    family=c.get("family", "Unknown"),
                    title=c["title"],
                    description=c.get("description"),
                    framework=c.get("framework", "NIST-800-53-Rev5"),
                    baseline=c.get("baseline"),
                )
                db.add(ctrl)
                created += 1
            await db.commit()
            return created, skipped

    created, skipped = _run(_ingest())
    console.print(f"✅ [green]Ingested {created} controls[/green] ({skipped} skipped)")


# ---------------------------------------------------------------------------
# ingest-evidence
# ---------------------------------------------------------------------------


@app.command("ingest-evidence")
def ingest_evidence(
    path: Path = typer.Argument(..., help="Path to evidence JSON file"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """📦 Ingest evidence items from a JSON file."""
    if not path.exists():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(code=1)

    with path.open() as f:
        data = json.load(f)

    items = data if isinstance(data, list) else data.get("evidence_items", [])
    console.print(f"[cyan]Found {len(items)} evidence items in {path}[/cyan]")

    if dry_run:
        table = Table("evidence_id", "title", "type", "source_system")
        for e in items:
            table.add_row(
                e.get("evidence_id", ""),
                e.get("title", "")[:50],
                e.get("evidence_type", ""),
                e.get("source_system", ""),
            )
        console.print(table)
        return

    async def _ingest():
        from sqlalchemy import select

        from app.db import AsyncSessionLocal
        from app.models import EvidenceItem

        async with AsyncSessionLocal() as db:
            created = 0
            for item in items:
                existing = await db.execute(
                    select(EvidenceItem).where(EvidenceItem.evidence_id == item["evidence_id"])
                )
                if existing.scalar_one_or_none():
                    continue
                ev = EvidenceItem(
                    evidence_id=item["evidence_id"],
                    title=item["title"],
                    evidence_type=item.get("evidence_type", "manual_upload"),
                    status=item.get("status", "valid"),
                    source_system=item.get("source_system"),
                    source_url=item.get("source_url"),
                )
                db.add(ev)
                created += 1
            await db.commit()
            return created

    created = _run(_ingest())
    console.print(f"✅ [green]Ingested {created} evidence items[/green]")


# ---------------------------------------------------------------------------
# evaluate-release
# ---------------------------------------------------------------------------


@app.command("evaluate-release")
def evaluate_release(
    release_id: str = typer.Option(..., "--release-id", help="Release identifier"),
    policy_file: Path | None = typer.Option(None, "--policy", help="Custom policy YAML file"),
    output: Path | None = typer.Option(None, "--output", help="Write result to JSON file"),
) -> None:
    """🔍 Evaluate release readiness against policy rules."""

    async def _evaluate():
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.db import AsyncSessionLocal
        from app.models import Release
        from app.services.policy_engine import (
            PolicyEngine,
            ReleaseContext,
            get_default_policy_engine,
        )

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Release)
                .where(Release.release_id == release_id)
                .options(
                    selectinload(Release.artifacts),
                    selectinload(Release.evidence_items),
                    selectinload(Release.exceptions),
                )
            )
            rel = result.scalar_one_or_none()
            if rel is None:
                return None

            engine = (
                PolicyEngine.from_yaml_file(str(policy_file))
                if policy_file
                else get_default_policy_engine()
            )

            ctx = ReleaseContext(
                release_id=release_id,
                artifacts=[
                    {
                        "artifact_id": a.artifact_id,
                        "has_sbom": a.has_sbom,
                        "has_provenance": a.has_provenance,
                        "has_signature": a.has_signature,
                        "critical_vulns": a.critical_vulns,
                        "high_vulns": a.high_vulns,
                    }
                    for a in rel.artifacts
                ],
                evidence_items=[
                    {"evidence_id": e.evidence_id, "collected_at": e.collected_at}
                    for e in rel.evidence_items
                ],
                open_blocking_exceptions=[
                    {"exception_id": exc.exception_id, "status": exc.status.value}
                    for exc in rel.exceptions
                ],
            )

            return engine.evaluate(ctx)

    console.print(Panel(f"[bold]Policy Evaluation — Release [cyan]{release_id}[/cyan][/bold]"))

    evaluation = _run(_evaluate())
    if evaluation is None:
        console.print(f"[red]Release {release_id} not found.[/red]")
        raise typer.Exit(code=1)

    # Summary
    status_icon = "✅" if evaluation.overall_passed else "❌"
    status_color = "green" if evaluation.overall_passed else "red"
    console.print(
        f"\n{status_icon} Overall: [{status_color}]"
        f"{'PASSED' if evaluation.overall_passed else 'BLOCKED'}[/{status_color}]"
        f"  |  Compliance Score: [bold]{evaluation.compliance_score}%[/bold]"
        f"  |  Blocking Failures: [bold]{evaluation.blocking_failures}[/bold]"
    )

    # Per-rule table
    table = Table(
        "Rule ID",
        "Name",
        "Severity",
        "Blocking",
        "Result",
        "Message",
        title="Policy Checks",
        show_lines=True,
    )
    for check in evaluation.checks:
        result_text = "[green]PASS[/green]" if check.passed else "[red]FAIL[/red]"
        table.add_row(
            check.rule_id,
            check.rule_name,
            check.severity,
            "Yes" if check.blocking else "No",
            result_text,
            check.message[:80],
        )
    console.print(table)

    # Optional output
    if output:
        output.write_text(json.dumps(evaluation.model_dump(mode="json"), indent=2, default=str))
        console.print(f"\n💾 Result saved to [blue]{output}[/blue]")

    raise typer.Exit(code=0 if evaluation.overall_passed else 1)


# ---------------------------------------------------------------------------
# generate-audit-bundle
# ---------------------------------------------------------------------------


@app.command("generate-audit-bundle")
def generate_audit_bundle(
    output: Path = typer.Option(
        Path("/tmp/aerlix-audit-bundle.json"), "--output", help="Output file path"
    ),
    release_id: str | None = typer.Option(None, "--release-id"),
    format: str = typer.Option("json", "--format", help="json or markdown"),
) -> None:
    """📄 Generate an audit bundle from current control plane state."""

    async def _generate():
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.db import AsyncSessionLocal
        from app.models import Control, EvidenceItem, ExceptionRecord, Incident
        from app.services.audit_exporter import AuditExporter

        async with AsyncSessionLocal() as db:
            exporter = AuditExporter(release_id=release_id)

            ctrl_result = await db.execute(
                select(Control).options(selectinload(Control.evidence_items))
            )
            controls = ctrl_result.scalars().all()
            exporter.add_controls(
                [
                    {
                        "control_id": c.control_id,
                        "title": c.title,
                        "family": c.family,
                        "baseline": c.baseline,
                        "status": c.implementations[0].status.value
                        if c.implementations
                        else "not_implemented",
                        "evidence_items": [
                            {"evidence_id": e.evidence_id} for e in c.evidence_items
                        ],
                    }
                    for c in controls
                ]
            )

            ev_result = await db.execute(select(EvidenceItem))
            evidence = ev_result.scalars().all()
            exporter.add_evidence_items(
                [
                    {
                        "evidence_id": e.evidence_id,
                        "title": e.title,
                        "evidence_type": e.evidence_type.value,
                        "status": e.status.value,
                        "source_system": e.source_system,
                        "collected_at": e.collected_at.isoformat() if e.collected_at else None,
                    }
                    for e in evidence
                ]
            )

            exc_result = await db.execute(select(ExceptionRecord))
            exceptions = exc_result.scalars().all()
            exporter.add_exceptions(
                [
                    {
                        "exception_id": e.exception_id,
                        "title": e.title,
                        "status": e.status.value,
                        "approver": e.approver,
                        "expires_at": e.expires_at.isoformat() if e.expires_at else None,
                        "justification": e.justification,
                    }
                    for e in exceptions
                ]
            )

            inc_result = await db.execute(select(Incident))
            incidents = inc_result.scalars().all()
            exporter.add_incidents(
                [
                    {
                        "incident_id": i.incident_id,
                        "title": i.title,
                        "severity": i.severity.value,
                        "status": i.status.value,
                    }
                    for i in incidents
                ]
            )

            return exporter

    console.print(Panel("[bold cyan]Generating Audit Bundle...[/bold cyan]"))
    exporter = _run(_generate())

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "markdown":
        exporter.save_markdown(str(out_path))
    else:
        exporter.save_json(str(out_path))

    console.print(f"\n✅ [green]Audit bundle written to[/green] [blue]{out_path}[/blue]")


# ---------------------------------------------------------------------------
# trace show
# ---------------------------------------------------------------------------


@trace_app.command("show")
def trace_show(
    requirement: str | None = typer.Option(None, "--requirement", help="Requirement ID"),
    control: str | None = typer.Option(None, "--control", help="Control ID"),
) -> None:
    """🔗 Show traceability graph for a requirement or control."""

    async def _trace(node_id: str):
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.db import AsyncSessionLocal
        from app.models import Control, Release, Requirement
        from app.services.traceability import build_engine_from_db_data

        async with AsyncSessionLocal() as db:
            reqs_result = await db.execute(
                select(Requirement).options(
                    selectinload(Requirement.controls),
                    selectinload(Requirement.test_cases),
                )
            )
            requirements = list(reqs_result.scalars().all())

            controls_result = await db.execute(
                select(Control).options(selectinload(Control.evidence_items))
            )
            controls = list(controls_result.scalars().all())

            releases_result = await db.execute(
                select(Release).options(
                    selectinload(Release.requirements),
                    selectinload(Release.artifacts),
                )
            )
            releases = list(releases_result.scalars().all())

            engine = build_engine_from_db_data(
                requirements=requirements,
                controls=controls,
                evidence_items=[],
                test_cases=[],
                releases=releases,
            )
            return engine, engine.to_schema(root_id=node_id)

    node_id = requirement or control
    if not node_id:
        console.print("[red]Specify --requirement or --control[/red]")
        raise typer.Exit(code=1)

    engine, graph = _run(_trace(node_id))

    console.print(Panel(f"[bold]Traceability Graph — [cyan]{node_id}[/cyan][/bold]"))

    table = Table("Node ID", "Type", "Label", "Status")
    for node in graph.nodes:
        table.add_row(node.node_id, node.node_type, node.label[:60], node.status or "")
    console.print(table)

    console.print(f"\n[dim]Edges: {len(graph.edges)}[/dim]")
    for edge in graph.edges[:20]:
        console.print(
            f"  [blue]{edge.source}[/blue] --[{edge.relationship}]--> [green]{edge.target}[/green]"
        )

    if len(graph.edges) > 20:
        console.print(f"  ... and {len(graph.edges) - 20} more")


# ---------------------------------------------------------------------------
# graph export
# ---------------------------------------------------------------------------


@app.command("graph-export")
def graph_export(
    output: Path = typer.Option(Path("/tmp/aerlix-graph.json"), "--output"),
) -> None:
    """📊 Export the full traceability graph to JSON."""

    async def _export():
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.db import AsyncSessionLocal
        from app.models import Control, Release, Requirement
        from app.services.traceability import build_engine_from_db_data

        async with AsyncSessionLocal() as db:
            reqs = list(
                (
                    await db.execute(
                        select(Requirement).options(
                            selectinload(Requirement.controls),
                            selectinload(Requirement.test_cases),
                        )
                    )
                )
                .scalars()
                .all()
            )
            controls = list(
                (await db.execute(select(Control).options(selectinload(Control.evidence_items))))
                .scalars()
                .all()
            )
            releases = list(
                (
                    await db.execute(
                        select(Release).options(
                            selectinload(Release.requirements),
                            selectinload(Release.artifacts),
                        )
                    )
                )
                .scalars()
                .all()
            )

            engine = build_engine_from_db_data(
                requirements=reqs,
                controls=controls,
                evidence_items=[],
                test_cases=[],
                releases=releases,
            )
            return engine.to_dict()

    graph_data = _run(_export())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(graph_data, indent=2, default=str))
    console.print(f"✅ Graph exported to [blue]{output}[/blue]")
    console.print(f"   Nodes: {len(graph_data['nodes'])}  |  Edges: {len(graph_data['edges'])}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
