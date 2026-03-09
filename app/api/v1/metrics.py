"""System metrics and statistics endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import (
    AuditBundle,
    Control,
    ControlImplementation,
    ControlStatus,
    EvidenceItem,
    EvidenceStatus,
    ExceptionRecord,
    ExceptionStatus,
    Incident,
    IncidentStatus,
    PolicyRule,
    Release,
    ReleaseStatus,
    Requirement,
    RequirementStatus,
    SBOMRecord,
    SystemComponent,
)

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("")
async def get_metrics(db: DbDep) -> dict:
    """Return real-time system metrics across all entities."""

    # Requirements
    req_total = (await db.execute(select(func.count()).select_from(Requirement))).scalar_one()
    req_verified = (
        await db.execute(
            select(func.count())
            .select_from(Requirement)
            .where(Requirement.status == RequirementStatus.VERIFIED)
        )
    ).scalar_one()
    req_implemented = (
        await db.execute(
            select(func.count())
            .select_from(Requirement)
            .where(Requirement.status == RequirementStatus.IMPLEMENTED)
        )
    ).scalar_one()

    # Controls
    ctrl_total = (await db.execute(select(func.count()).select_from(Control))).scalar_one()
    ctrl_implemented = (
        await db.execute(
            select(func.count())
            .select_from(ControlImplementation)
            .where(ControlImplementation.status == ControlStatus.IMPLEMENTED)
        )
    ).scalar_one()

    # Evidence
    ev_total = (await db.execute(select(func.count()).select_from(EvidenceItem))).scalar_one()
    ev_valid = (
        await db.execute(
            select(func.count())
            .select_from(EvidenceItem)
            .where(EvidenceItem.status == EvidenceStatus.VALID)
        )
    ).scalar_one()
    ev_expired = (
        await db.execute(
            select(func.count())
            .select_from(EvidenceItem)
            .where(EvidenceItem.status == EvidenceStatus.EXPIRED)
        )
    ).scalar_one()

    # Releases
    rel_total = (await db.execute(select(func.count()).select_from(Release))).scalar_one()
    rel_approved = (
        await db.execute(
            select(func.count())
            .select_from(Release)
            .where(Release.status == ReleaseStatus.APPROVED)
        )
    ).scalar_one()
    rel_blocked = (
        await db.execute(
            select(func.count()).select_from(Release).where(Release.status == ReleaseStatus.BLOCKED)
        )
    ).scalar_one()

    # Incidents and exceptions
    inc_open = (
        await db.execute(
            select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.OPEN)
        )
    ).scalar_one()
    exc_open = (
        await db.execute(
            select(func.count())
            .select_from(ExceptionRecord)
            .where(ExceptionRecord.status == ExceptionStatus.OPEN)
        )
    ).scalar_one()

    # SBOM
    sbom_total = (await db.execute(select(func.count()).select_from(SBOMRecord))).scalar_one()

    # Components
    comp_total = (await db.execute(select(func.count()).select_from(SystemComponent))).scalar_one()

    # Policy rules
    policy_total = (await db.execute(select(func.count()).select_from(PolicyRule))).scalar_one()

    # Audit bundles
    audit_total = (await db.execute(select(func.count()).select_from(AuditBundle))).scalar_one()

    # Derived scores
    req_completion_pct = round((req_verified / req_total) * 100, 1) if req_total else 0.0
    ev_validity_pct = round((ev_valid / ev_total) * 100, 1) if ev_total else 0.0
    release_approval_pct = round((rel_approved / rel_total) * 100, 1) if rel_total else 0.0

    return {
        "requirements": {
            "total": req_total,
            "verified": req_verified,
            "implemented": req_implemented,
            "completion_pct": req_completion_pct,
        },
        "controls": {
            "total": ctrl_total,
            "implementations_satisfied": ctrl_implemented,
        },
        "evidence": {
            "total": ev_total,
            "valid": ev_valid,
            "expired": ev_expired,
            "validity_pct": ev_validity_pct,
        },
        "releases": {
            "total": rel_total,
            "approved": rel_approved,
            "blocked": rel_blocked,
            "approval_pct": release_approval_pct,
        },
        "incidents": {
            "open": inc_open,
        },
        "exceptions": {
            "open": exc_open,
        },
        "supply_chain": {
            "sbom_records": sbom_total,
            "system_components": comp_total,
        },
        "governance": {
            "policy_rules": policy_total,
            "audit_bundles": audit_total,
        },
    }
