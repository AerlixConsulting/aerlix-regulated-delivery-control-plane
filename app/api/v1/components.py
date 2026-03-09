"""System components endpoints."""

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import SystemComponent
from app.schemas import SystemComponentCreate, SystemComponentRead

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[SystemComponentRead])
async def list_components(
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    component_type: str | None = None,
) -> list[SystemComponent]:
    q = select(SystemComponent)
    if component_type:
        q = q.where(SystemComponent.component_type == component_type)
    q = q.offset(skip).limit(limit).order_by(SystemComponent.name)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{component_id}", response_model=SystemComponentRead)
async def get_component(component_id: str, db: DbDep) -> SystemComponent:
    result = await db.execute(select(SystemComponent).where(SystemComponent.name == component_id))
    comp = result.scalar_one_or_none()
    if comp is None:
        # Try by UUID string representation
        try:

            uid = _uuid.UUID(component_id)
            result2 = await db.execute(select(SystemComponent).where(SystemComponent.id == uid))
            comp = result2.scalar_one_or_none()
        except ValueError:
            pass
    if comp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System component not found"
        )
    return comp


@router.post("", response_model=SystemComponentRead, status_code=status.HTTP_201_CREATED)
async def create_component(payload: SystemComponentCreate, db: DbDep) -> SystemComponent:
    existing = await db.execute(select(SystemComponent).where(SystemComponent.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"System component '{payload.name}' already exists",
        )
    comp = SystemComponent(**payload.model_dump())
    db.add(comp)
    await db.commit()
    await db.refresh(comp)
    return comp


@router.put("/{component_id}", response_model=SystemComponentRead)
async def update_component(
    component_id: str, payload: SystemComponentCreate, db: DbDep
) -> SystemComponent:
    try:

        uid = _uuid.UUID(component_id)
        result = await db.execute(select(SystemComponent).where(SystemComponent.id == uid))
    except ValueError:
        result = await db.execute(
            select(SystemComponent).where(SystemComponent.name == component_id)
        )
    comp = result.scalar_one_or_none()
    if comp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System component not found"
        )
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(comp, k, v)
    await db.commit()
    await db.refresh(comp)
    return comp


@router.patch("/{component_id}", response_model=SystemComponentRead)
async def patch_component(
    component_id: str, payload: SystemComponentCreate, db: DbDep
) -> SystemComponent:
    try:

        uid = _uuid.UUID(component_id)
        result = await db.execute(select(SystemComponent).where(SystemComponent.id == uid))
    except ValueError:
        result = await db.execute(
            select(SystemComponent).where(SystemComponent.name == component_id)
        )
    comp = result.scalar_one_or_none()
    if comp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System component not found"
        )
    for k, v in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(comp, k, v)
    await db.commit()
    await db.refresh(comp)
    return comp


@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component(component_id: str, db: DbDep) -> None:
    try:

        uid = _uuid.UUID(component_id)
        result = await db.execute(select(SystemComponent).where(SystemComponent.id == uid))
    except ValueError:
        result = await db.execute(
            select(SystemComponent).where(SystemComponent.name == component_id)
        )
    comp = result.scalar_one_or_none()
    if comp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="System component not found"
        )
    await db.delete(comp)
    await db.commit()
