"""Evidence endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import EvidenceItem
from app.schemas import EvidenceItemCreate, EvidenceItemRead

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[EvidenceItemRead])
async def list_evidence(
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    evidence_type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    control_id: str | None = None,
) -> list[EvidenceItem]:
    q = select(EvidenceItem)
    if evidence_type:
        q = q.where(EvidenceItem.evidence_type == evidence_type)
    if status_filter:
        q = q.where(EvidenceItem.status == status_filter)
    q = q.offset(skip).limit(limit).order_by(EvidenceItem.collected_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{evidence_id}", response_model=EvidenceItemRead)
async def get_evidence(evidence_id: str, db: DbDep) -> EvidenceItem:
    result = await db.execute(
        select(EvidenceItem).where(EvidenceItem.evidence_id == evidence_id)
    )
    ev = result.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence item not found")
    return ev


@router.post("", response_model=EvidenceItemRead, status_code=status.HTTP_201_CREATED)
async def create_evidence(payload: EvidenceItemCreate, db: DbDep) -> EvidenceItem:
    existing = await db.execute(
        select(EvidenceItem).where(EvidenceItem.evidence_id == payload.evidence_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Evidence item {payload.evidence_id} already exists",
        )
    data = payload.model_dump(by_alias=False)
    # Handle aliased field
    metadata_val = data.pop("metadata_", None)
    ev = EvidenceItem(**data, metadata_=metadata_val)
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.put("/{evidence_id}", response_model=EvidenceItemRead)
async def update_evidence(evidence_id: str, payload: EvidenceItemCreate, db: DbDep) -> EvidenceItem:
    result = await db.execute(
        select(EvidenceItem).where(EvidenceItem.evidence_id == evidence_id)
    )
    ev = result.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence item not found")
    data = payload.model_dump(exclude_unset=True, by_alias=False)
    for k, v in data.items():
        setattr(ev, k, v)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(evidence_id: str, db: DbDep) -> None:
    result = await db.execute(
        select(EvidenceItem).where(EvidenceItem.evidence_id == evidence_id)
    )
    ev = result.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence item not found")
    await db.delete(ev)
    await db.commit()
