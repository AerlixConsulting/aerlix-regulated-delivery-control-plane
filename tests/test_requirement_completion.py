"""Tests for requirement completion flag."""

import uuid
from datetime import UTC, datetime

from app.models import Requirement, RequirementStatus, RequirementType
from app.schemas import RequirementRead


def test_requirement_is_completed_flag() -> None:
    now = datetime.now(tz=UTC)
    verified_req = Requirement(
        id=uuid.uuid4(),
        req_id="REQ-100",
        title="Verified requirement",
        req_type=RequirementType.SYSTEM,
        status=RequirementStatus.VERIFIED,
        created_at=now,
        updated_at=now,
    )
    assert verified_req.is_completed is True
    verified_schema = RequirementRead.model_validate(verified_req)
    assert verified_schema.is_completed is True

    draft_req = Requirement(
        id=uuid.uuid4(),
        req_id="REQ-101",
        title="Draft requirement",
        req_type=RequirementType.SYSTEM,
        status=RequirementStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )
    assert draft_req.is_completed is False
    draft_schema = RequirementRead.model_validate(draft_req)
    assert draft_schema.is_completed is False
