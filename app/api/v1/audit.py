"""Audit bundle endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import AuditBundle, Control, EvidenceItem, ExceptionRecord, Incident, Release
from app.services.audit_exporter import AuditExporter

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def _build_exporter(db: AsyncSession, release_id: str | None = None) -> AuditExporter:
    """Assemble an AuditExporter populated with all required data."""
    exporter = AuditExporter(release_id=release_id)

    # Controls
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
                "status": (
                    c.implementations[0].status.value
                    if c.implementations
                    else "not_implemented"
                ),
                "evidence_items": [
                    {"evidence_id": e.evidence_id, "title": e.title} for e in c.evidence_items
                ],
            }
            for c in controls
        ]
    )

    # Evidence
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

    # Exceptions
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

    # Incidents
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

    # Release (if specified)
    if release_id:
        rel_result = await db.execute(
            select(Release)
            .where(Release.release_id == release_id)
            .options(selectinload(Release.artifacts))
        )
        rel = rel_result.scalar_one_or_none()
        if rel:
            exporter.add_release(
                {
                    "release_id": rel.release_id,
                    "version": rel.version,
                    "status": rel.status.value,
                }
            )
            exporter.add_artifacts(
                [
                    {
                        "artifact_id": a.artifact_id,
                        "name": a.name,
                        "has_sbom": a.has_sbom,
                        "has_provenance": a.has_provenance,
                        "has_signature": a.has_signature,
                        "critical_vulns": a.critical_vulns,
                        "high_vulns": a.high_vulns,
                    }
                    for a in rel.artifacts
                ]
            )
            if rel.policy_evaluation:
                exporter.add_policy_evaluation(rel.policy_evaluation)

    return exporter


@router.post("/generate")
async def generate_audit_bundle(
    db: DbDep,
    release_id: str | None = None,
    format: str = "json",
) -> Response:
    """Generate and return an audit bundle in JSON or Markdown format."""
    exporter = await _build_exporter(db, release_id=release_id)

    if format == "markdown":
        content = exporter.to_markdown()
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": 'attachment; filename="audit-bundle.md"'},
        )
    else:
        content = exporter.to_json()
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="audit-bundle.json"'},
        )


@router.get("/bundles")
async def list_audit_bundles(db: DbDep) -> list[dict]:
    """List previously generated audit bundles."""
    result = await db.execute(select(AuditBundle).order_by(AuditBundle.generated_at.desc()))
    bundles = result.scalars().all()
    return [
        {
            "bundle_id": b.bundle_id,
            "title": b.title,
            "release_id": str(b.release_id) if b.release_id else None,
            "generated_at": b.generated_at.isoformat(),
            "generated_by": b.generated_by,
        }
        for b in bundles
    ]


@router.get("/summary")
async def audit_summary(db: DbDep) -> dict:
    """Return a high-level audit readiness summary."""
    exporter = await _build_exporter(db)
    bundle = exporter.build_bundle()
    gaps = bundle["gaps"]
    ctrl_summary = bundle["control_summary"]
    ev_index = bundle["evidence_index"]
    exc_reg = bundle["exception_register"]

    total_possible = (
        ctrl_summary["total_controls"]
        + ev_index["total_evidence_items"]
    )
    if total_possible:
        implemented = ctrl_summary["implemented_count"]
        valid_ev = ev_index.get("by_status", {}).get("valid", 0)
        completeness = round(((implemented + valid_ev) / total_possible) * 100, 1)
    else:
        completeness = 0.0

    return {
        "audit_completeness_score": completeness,
        "total_gaps": gaps["total_gaps"],
        "open_exceptions": exc_reg["open_exceptions"],
        "control_summary": ctrl_summary,
        "evidence_summary": {
            "total": ev_index["total_evidence_items"],
            "by_status": ev_index.get("by_status", {}),
        },
    }
