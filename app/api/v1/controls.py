"""Controls endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Control, ControlImplementation
from app.schemas import (
    ControlCreate,
    ControlDetail,
    ControlImplementationCreate,
    ControlImplementationRead,
    ControlRead,
)

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[ControlRead])
async def list_controls(
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    family: str | None = None,
    baseline: str | None = None,
) -> list[Control]:
    q = select(Control)
    if family:
        q = q.where(Control.family.ilike(f"%{family}%"))
    if baseline:
        q = q.where(Control.baseline == baseline)
    q = q.offset(skip).limit(limit).order_by(Control.control_id)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{control_id}", response_model=ControlDetail)
async def get_control(control_id: str, db: DbDep) -> Control:
    result = await db.execute(
        select(Control)
        .where(Control.control_id == control_id)
        .options(
            selectinload(Control.requirements),
            selectinload(Control.implementations),
            selectinload(Control.evidence_items),
        )
    )
    ctrl = result.scalar_one_or_none()
    if ctrl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    return ctrl


@router.post("", response_model=ControlRead, status_code=status.HTTP_201_CREATED)
async def create_control(payload: ControlCreate, db: DbDep) -> Control:
    existing = await db.execute(select(Control).where(Control.control_id == payload.control_id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Control {payload.control_id} already exists",
        )
    ctrl = Control(**payload.model_dump())
    db.add(ctrl)
    await db.commit()
    await db.refresh(ctrl)
    return ctrl


@router.put("/{control_id}", response_model=ControlRead)
async def update_control(control_id: str, payload: ControlCreate, db: DbDep) -> Control:
    result = await db.execute(select(Control).where(Control.control_id == control_id))
    ctrl = result.scalar_one_or_none()
    if ctrl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ctrl, k, v)
    await db.commit()
    await db.refresh(ctrl)
    return ctrl


@router.patch("/{control_id}", response_model=ControlRead)
async def patch_control(control_id: str, payload: ControlCreate, db: DbDep) -> Control:
    result = await db.execute(select(Control).where(Control.control_id == control_id))
    ctrl = result.scalar_one_or_none()
    if ctrl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    for k, v in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(ctrl, k, v)
    await db.commit()
    await db.refresh(ctrl)
    return ctrl


@router.delete("/{control_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_control(control_id: str, db: DbDep) -> None:
    result = await db.execute(select(Control).where(Control.control_id == control_id))
    ctrl = result.scalar_one_or_none()
    if ctrl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    await db.delete(ctrl)
    await db.commit()


# --- Implementations ---


@router.get("/{control_id}/implementations", response_model=list[ControlImplementationRead])
async def list_implementations(control_id: str, db: DbDep) -> list[ControlImplementation]:
    result = await db.execute(select(Control).where(Control.control_id == control_id))
    ctrl = result.scalar_one_or_none()
    if ctrl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    impl_result = await db.execute(
        select(ControlImplementation).where(ControlImplementation.control_id == ctrl.id)
    )
    return list(impl_result.scalars().all())


@router.post(
    "/{control_id}/implementations",
    response_model=ControlImplementationRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_implementation(
    control_id: str, payload: ControlImplementationCreate, db: DbDep
) -> ControlImplementation:
    result = await db.execute(select(Control).where(Control.control_id == control_id))
    ctrl = result.scalar_one_or_none()
    if ctrl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    impl = ControlImplementation(**payload.model_dump(), control_id=ctrl.id)
    db.add(impl)
    await db.commit()
    await db.refresh(impl)
    return impl
