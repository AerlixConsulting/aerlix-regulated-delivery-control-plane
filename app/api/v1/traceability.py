"""Traceability endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Control, Release, Requirement
from app.schemas import TraceabilityGraph
from app.services.traceability import TraceabilityEngine, build_engine_from_db_data

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def _build_engine(db: AsyncSession) -> TraceabilityEngine:
    reqs_result = await db.execute(
        select(Requirement).options(
            selectinload(Requirement.controls),
            selectinload(Requirement.test_cases),
        )
    )
    requirements = list(reqs_result.scalars().all())

    controls_result = await db.execute(
        select(Control).options(
            selectinload(Control.evidence_items),
        )
    )
    controls = list(controls_result.scalars().all())

    releases_result = await db.execute(
        select(Release).options(
            selectinload(Release.requirements),
            selectinload(Release.artifacts),
        )
    )
    releases = list(releases_result.scalars().all())

    return build_engine_from_db_data(
        requirements=requirements,
        controls=controls,
        evidence_items=[],
        test_cases=[],
        releases=releases,
    )


@router.get("/graph", response_model=TraceabilityGraph)
async def get_full_graph(db: DbDep) -> TraceabilityGraph:
    """Return the complete traceability graph."""
    engine = await _build_engine(db)
    return engine.to_schema()


@router.get("/graph/requirement/{req_id}", response_model=TraceabilityGraph)
async def get_requirement_trace(req_id: str, db: DbDep) -> TraceabilityGraph:
    """Return traceability subgraph centered on a requirement."""
    engine = await _build_engine(db)
    if req_id not in engine.graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirement {req_id} not found in traceability graph",
        )
    return engine.to_schema(root_id=req_id)


@router.get("/graph/control/{control_id}", response_model=TraceabilityGraph)
async def get_control_trace(control_id: str, db: DbDep) -> TraceabilityGraph:
    """Return traceability subgraph centered on a control."""
    engine = await _build_engine(db)
    if control_id not in engine.graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control {control_id} not found in traceability graph",
        )
    return engine.to_schema(root_id=control_id)


@router.get("/graph/release/{release_id}", response_model=TraceabilityGraph)
async def get_release_trace(release_id: str, db: DbDep) -> TraceabilityGraph:
    """Return traceability subgraph centered on a release."""
    engine = await _build_engine(db)
    if release_id not in engine.graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Release {release_id} not found in traceability graph",
        )
    return engine.to_schema(root_id=release_id)


@router.get("/gaps")
async def get_traceability_gaps(db: DbDep) -> dict:
    """Return gap analysis: untested requirements, controls without evidence, etc."""
    engine = await _build_engine(db)
    return {
        "untested_requirements": engine.requirements_without_tests(),
        "unmapped_requirements": engine.requirements_without_controls(),
        "controls_without_evidence": engine.controls_without_evidence(),
        "stats": engine.coverage_stats(),
    }


@router.get("/stats")
async def get_traceability_stats(db: DbDep) -> dict:
    """Return high-level traceability coverage statistics."""
    engine = await _build_engine(db)
    return engine.coverage_stats()
