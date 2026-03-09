"""SBOM (Software Bill of Materials) endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import SBOMRecord
from app.schemas import SBOMRecordCreate, SBOMRecordRead

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[SBOMRecordRead])
async def list_sbom_records(
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    sbom_format: str | None = Query(None, alias="format"),
) -> list[SBOMRecord]:
    q = select(SBOMRecord)
    if sbom_format:
        q = q.where(SBOMRecord.format == sbom_format)
    q = q.offset(skip).limit(limit).order_by(SBOMRecord.ingested_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{sbom_id}", response_model=SBOMRecordRead)
async def get_sbom_record(sbom_id: str, db: DbDep) -> SBOMRecord:
    result = await db.execute(select(SBOMRecord).where(SBOMRecord.sbom_id == sbom_id))
    sbom = result.scalar_one_or_none()
    if sbom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SBOM record not found")
    return sbom


@router.post("", response_model=SBOMRecordRead, status_code=status.HTTP_201_CREATED)
async def create_sbom_record(payload: SBOMRecordCreate, db: DbDep) -> SBOMRecord:
    existing = await db.execute(select(SBOMRecord).where(SBOMRecord.sbom_id == payload.sbom_id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SBOM record {payload.sbom_id} already exists",
        )
    sbom = SBOMRecord(**payload.model_dump())
    db.add(sbom)
    await db.commit()
    await db.refresh(sbom)
    return sbom


@router.put("/{sbom_id}", response_model=SBOMRecordRead)
async def update_sbom_record(sbom_id: str, payload: SBOMRecordCreate, db: DbDep) -> SBOMRecord:
    result = await db.execute(select(SBOMRecord).where(SBOMRecord.sbom_id == sbom_id))
    sbom = result.scalar_one_or_none()
    if sbom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SBOM record not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(sbom, k, v)
    await db.commit()
    await db.refresh(sbom)
    return sbom


@router.patch("/{sbom_id}", response_model=SBOMRecordRead)
async def patch_sbom_record(sbom_id: str, payload: SBOMRecordCreate, db: DbDep) -> SBOMRecord:
    result = await db.execute(select(SBOMRecord).where(SBOMRecord.sbom_id == sbom_id))
    sbom = result.scalar_one_or_none()
    if sbom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SBOM record not found")
    for k, v in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(sbom, k, v)
    await db.commit()
    await db.refresh(sbom)
    return sbom


@router.delete("/{sbom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sbom_record(sbom_id: str, db: DbDep) -> None:
    result = await db.execute(select(SBOMRecord).where(SBOMRecord.sbom_id == sbom_id))
    sbom = result.scalar_one_or_none()
    if sbom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SBOM record not found")
    await db.delete(sbom)
    await db.commit()
