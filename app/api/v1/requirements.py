"""Requirements endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Requirement
from app.schemas import RequirementCreate, RequirementDetail, RequirementRead

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[RequirementRead])
async def list_requirements(
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: str | None = None,
    req_type: str | None = None,
) -> list[Requirement]:
    q = select(Requirement)
    if status:
        q = q.where(Requirement.status == status)
    if req_type:
        q = q.where(Requirement.req_type == req_type)
    q = q.offset(skip).limit(limit).order_by(Requirement.req_id)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/count")
async def count_requirements(db: DbDep) -> dict:
    result = await db.execute(select(func.count()).select_from(Requirement))
    return {"count": result.scalar_one()}


@router.get("/{req_id}", response_model=RequirementDetail)
async def get_requirement(req_id: str, db: DbDep) -> Requirement:
    result = await db.execute(
        select(Requirement)
        .where(Requirement.req_id == req_id)
        .options(
            selectinload(Requirement.controls),
            selectinload(Requirement.test_cases),
        )
    )
    req = result.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
    return req


@router.post("", response_model=RequirementRead, status_code=status.HTTP_201_CREATED)
async def create_requirement(payload: RequirementCreate, db: DbDep) -> Requirement:
    existing = await db.execute(
        select(Requirement).where(Requirement.req_id == payload.req_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Requirement {payload.req_id} already exists",
        )
    req = Requirement(**payload.model_dump())
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@router.put("/{req_id}", response_model=RequirementRead)
async def update_requirement(req_id: str, payload: RequirementCreate, db: DbDep) -> Requirement:
    result = await db.execute(select(Requirement).where(Requirement.req_id == req_id))
    req = result.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(req, k, v)
    await db.commit()
    await db.refresh(req)
    return req


@router.delete("/{req_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(req_id: str, db: DbDep) -> None:
    result = await db.execute(select(Requirement).where(Requirement.req_id == req_id))
    req = result.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
    await db.delete(req)
    await db.commit()
