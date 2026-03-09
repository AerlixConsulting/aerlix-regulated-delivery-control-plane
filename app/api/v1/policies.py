"""Policy evaluation endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Release
from app.schemas import PolicyEvaluationResult
from app.services.policy_engine import ReleaseContext, get_default_policy_engine

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/rules", response_model=list[dict])
async def list_default_rules() -> list[dict]:
    """Return the default policy ruleset."""
    engine = get_default_policy_engine()
    return [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "severity": r.severity,
            "blocking": r.blocking,
            "enabled": r.enabled,
            "condition_type": r.condition.condition_type,
        }
        for r in engine.rules
    ]


@router.post("/evaluate/{release_id}", response_model=PolicyEvaluationResult)
async def evaluate_release_policy(release_id: str, db: DbDep) -> PolicyEvaluationResult:
    """Evaluate all policy rules for a release and return the full result."""
    result = await db.execute(
        select(Release)
        .where(Release.release_id == release_id)
        .options(
            selectinload(Release.artifacts),
            selectinload(Release.requirements),
            selectinload(Release.evidence_items),
            selectinload(Release.exceptions),
        )
    )
    rel = result.scalar_one_or_none()
    if rel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    # Build evaluation context from release data
    artifacts = [
        {
            "artifact_id": a.artifact_id,
            "has_sbom": a.has_sbom,
            "has_provenance": a.has_provenance,
            "has_signature": a.has_signature,
            "critical_vulns": a.critical_vulns,
            "high_vulns": a.high_vulns,
        }
        for a in rel.artifacts
    ]

    evidence_items = [
        {
            "evidence_id": e.evidence_id,
            "collected_at": e.collected_at,
            "status": e.status.value if hasattr(e.status, "value") else e.status,
        }
        for e in rel.evidence_items
    ]

    open_exceptions = [
        {
            "exception_id": exc.exception_id,
            "status": exc.status.value if hasattr(exc.status, "value") else exc.status,
        }
        for exc in rel.exceptions
        if exc.status.value == "open"
    ]

    ctx = ReleaseContext(
        release_id=release_id,
        artifacts=artifacts,
        evidence_items=evidence_items,
        open_blocking_exceptions=open_exceptions,
    )

    engine = get_default_policy_engine()
    evaluation = engine.evaluate(ctx)

    # Persist result to release
    rel.policy_evaluation = evaluation.model_dump(mode="json")
    rel.compliance_score = evaluation.compliance_score
    if evaluation.overall_passed:
        rel.status = "approved"  # type: ignore[assignment]
    else:
        rel.status = "blocked"  # type: ignore[assignment]
    await db.commit()

    return evaluation
