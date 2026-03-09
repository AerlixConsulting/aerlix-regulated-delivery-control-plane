"""Incidents and exceptions endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import ExceptionRecord, Incident
from app.schemas import (
    ExceptionRecordCreate,
    ExceptionRecordRead,
    IncidentCreate,
    IncidentRead,
)

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]

# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    incident_status: str | None = Query(None, alias="status"),
    severity: str | None = None,
) -> list[Incident]:
    q = select(Incident)
    if incident_status:
        q = q.where(Incident.status == incident_status)
    if severity:
        q = q.where(Incident.severity == severity)
    q = q.offset(skip).limit(limit).order_by(Incident.detected_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: str, db: DbDep) -> Incident:
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    inc = result.scalar_one_or_none()
    if inc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return inc


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def create_incident(payload: IncidentCreate, db: DbDep) -> Incident:
    existing = await db.execute(select(Incident).where(Incident.incident_id == payload.incident_id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Incident {payload.incident_id} already exists",
        )
    inc = Incident(**payload.model_dump())
    db.add(inc)
    await db.commit()
    await db.refresh(inc)
    return inc


@router.put("/{incident_id}", response_model=IncidentRead)
async def update_incident(incident_id: str, payload: IncidentCreate, db: DbDep) -> Incident:
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    inc = result.scalar_one_or_none()
    if inc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(inc, k, v)
    await db.commit()
    await db.refresh(inc)
    return inc


@router.patch("/{incident_id}", response_model=IncidentRead)
async def patch_incident(incident_id: str, payload: IncidentCreate, db: DbDep) -> Incident:
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    inc = result.scalar_one_or_none()
    if inc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    for k, v in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(inc, k, v)
    await db.commit()
    await db.refresh(inc)
    return inc


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: str, db: DbDep) -> None:
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    inc = result.scalar_one_or_none()
    if inc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await db.delete(inc)
    await db.commit()


# ---------------------------------------------------------------------------
# Exceptions (sub-resource)
# ---------------------------------------------------------------------------


@router.get("/exceptions/list", response_model=list[ExceptionRecordRead])
async def list_exceptions(
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    exc_status: str | None = Query(None, alias="status"),
) -> list[ExceptionRecord]:
    q = select(ExceptionRecord)
    if exc_status:
        q = q.where(ExceptionRecord.status == exc_status)
    q = q.offset(skip).limit(limit).order_by(ExceptionRecord.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/exceptions/{exception_id}", response_model=ExceptionRecordRead)
async def get_exception(exception_id: str, db: DbDep) -> ExceptionRecord:
    result = await db.execute(
        select(ExceptionRecord).where(ExceptionRecord.exception_id == exception_id)
    )
    exc = result.scalar_one_or_none()
    if exc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exception record not found"
        )
    return exc


@router.post(
    "/exceptions",
    response_model=ExceptionRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_exception(payload: ExceptionRecordCreate, db: DbDep) -> ExceptionRecord:
    existing = await db.execute(
        select(ExceptionRecord).where(ExceptionRecord.exception_id == payload.exception_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Exception record {payload.exception_id} already exists",
        )
    exc = ExceptionRecord(**payload.model_dump())
    db.add(exc)
    await db.commit()
    await db.refresh(exc)
    return exc


@router.put("/exceptions/{exception_id}", response_model=ExceptionRecordRead)
async def update_exception(
    exception_id: str, payload: ExceptionRecordCreate, db: DbDep
) -> ExceptionRecord:
    result = await db.execute(
        select(ExceptionRecord).where(ExceptionRecord.exception_id == exception_id)
    )
    exc = result.scalar_one_or_none()
    if exc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exception record not found"
        )
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(exc, k, v)
    await db.commit()
    await db.refresh(exc)
    return exc


@router.patch("/exceptions/{exception_id}", response_model=ExceptionRecordRead)
async def patch_exception(
    exception_id: str, payload: ExceptionRecordCreate, db: DbDep
) -> ExceptionRecord:
    result = await db.execute(
        select(ExceptionRecord).where(ExceptionRecord.exception_id == exception_id)
    )
    exc = result.scalar_one_or_none()
    if exc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exception record not found"
        )
    for k, v in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(exc, k, v)
    await db.commit()
    await db.refresh(exc)
    return exc


@router.delete("/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exception(exception_id: str, db: DbDep) -> None:
    result = await db.execute(
        select(ExceptionRecord).where(ExceptionRecord.exception_id == exception_id)
    )
    exc = result.scalar_one_or_none()
    if exc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exception record not found"
        )
    await db.delete(exc)
    await db.commit()
