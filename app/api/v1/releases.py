"""Releases endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Release
from app.schemas import ReleaseCreate, ReleaseDetail, ReleaseRead

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[ReleaseRead])
async def list_releases(
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    release_status: str | None = Query(None, alias="status"),
) -> list[Release]:
    q = select(Release)
    if release_status:
        q = q.where(Release.status == release_status)
    q = q.offset(skip).limit(limit).order_by(Release.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{release_id}", response_model=ReleaseDetail)
async def get_release(release_id: str, db: DbDep) -> Release:
    result = await db.execute(
        select(Release)
        .where(Release.release_id == release_id)
        .options(
            selectinload(Release.requirements),
            selectinload(Release.evidence_items),
            selectinload(Release.artifacts),
            selectinload(Release.exceptions),
        )
    )
    rel = result.scalar_one_or_none()
    if rel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return rel


@router.post("", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
async def create_release(payload: ReleaseCreate, db: DbDep) -> Release:
    existing = await db.execute(select(Release).where(Release.release_id == payload.release_id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Release {payload.release_id} already exists",
        )
    rel = Release(**payload.model_dump())
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return rel


@router.put("/{release_id}", response_model=ReleaseRead)
async def update_release(release_id: str, payload: ReleaseCreate, db: DbDep) -> Release:
    result = await db.execute(select(Release).where(Release.release_id == release_id))
    rel = result.scalar_one_or_none()
    if rel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(rel, k, v)
    await db.commit()
    await db.refresh(rel)
    return rel


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_release(release_id: str, db: DbDep) -> None:
    result = await db.execute(select(Release).where(Release.release_id == release_id))
    rel = result.scalar_one_or_none()
    if rel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    await db.delete(rel)
    await db.commit()
