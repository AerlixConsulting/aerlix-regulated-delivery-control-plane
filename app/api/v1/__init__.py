"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    audit,
    controls,
    evidence,
    policies,
    releases,
    requirements,
    traceability,
)

router = APIRouter()

router.include_router(requirements.router, prefix="/requirements", tags=["Requirements"])
router.include_router(controls.router, prefix="/controls", tags=["Controls"])
router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
router.include_router(releases.router, prefix="/releases", tags=["Releases"])
router.include_router(traceability.router, prefix="/traceability", tags=["Traceability"])
router.include_router(policies.router, prefix="/policies", tags=["Policies"])
router.include_router(audit.router, prefix="/audit", tags=["Audit"])
