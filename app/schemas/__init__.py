"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    ControlStatus,
    EvidenceStatus,
    EvidenceType,
    ExceptionStatus,
    IncidentStatus,
    ReleaseStatus,
    RequirementStatus,
    RequirementType,
    SeverityLevel,
)

# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------


class OwnerBase(BaseSchema):
    name: str
    email: str | None = None
    role: str | None = None
    team: str | None = None


class OwnerCreate(OwnerBase):
    pass


class OwnerRead(OwnerBase):
    id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# SystemComponent
# ---------------------------------------------------------------------------


class SystemComponentBase(BaseSchema):
    name: str
    component_type: str
    description: str | None = None
    version: str | None = None
    owner_id: uuid.UUID | None = None


class SystemComponentCreate(SystemComponentBase):
    pass


class SystemComponentRead(SystemComponentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------


class RequirementBase(BaseSchema):
    req_id: str
    title: str
    description: str | None = None
    req_type: RequirementType = RequirementType.SYSTEM
    status: RequirementStatus = RequirementStatus.DRAFT
    priority: str | None = None
    source: str | None = None
    owner_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None


class RequirementCreate(RequirementBase):
    pass


class RequirementRead(RequirementBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_completed: bool


class RequirementDetail(RequirementRead):
    controls: list["ControlRead"] = []
    test_cases: list["TestCaseRead"] = []


# ---------------------------------------------------------------------------
# Control
# ---------------------------------------------------------------------------


class ControlBase(BaseSchema):
    control_id: str
    family: str
    title: str
    description: str | None = None
    framework: str = "NIST-800-53-Rev5"
    baseline: str | None = None


class ControlCreate(ControlBase):
    pass


class ControlRead(ControlBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ControlDetail(ControlRead):
    requirements: list["RequirementRead"] = []
    implementations: list["ControlImplementationRead"] = []
    evidence_items: list["EvidenceItemRead"] = []


class ControlImplementationBase(BaseSchema):
    control_id: uuid.UUID
    component_id: uuid.UUID | None = None
    status: ControlStatus = ControlStatus.NOT_IMPLEMENTED
    implementation_notes: str | None = None
    responsible_role: str | None = None
    inherited_from: str | None = None


class ControlImplementationCreate(ControlImplementationBase):
    pass


class ControlImplementationRead(ControlImplementationBase):
    id: uuid.UUID
    last_assessed: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class EvidenceItemBase(BaseSchema):
    evidence_id: str
    title: str
    evidence_type: EvidenceType
    status: EvidenceStatus = EvidenceStatus.PENDING
    source_system: str | None = None
    source_url: str | None = None
    content_hash: str | None = None
    expires_at: datetime | None = None
    metadata_: dict | None = Field(None, alias="metadata")
    control_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class EvidenceItemCreate(EvidenceItemBase):
    pass


class EvidenceItemRead(EvidenceItemBase):
    id: uuid.UUID
    collected_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Test Case
# ---------------------------------------------------------------------------


class TestCaseBase(BaseSchema):
    test_id: str
    name: str
    description: str | None = None
    test_type: str | None = None
    requirement_id: uuid.UUID | None = None
    last_result: str | None = None
    last_run_at: datetime | None = None


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseRead(TestCaseBase):
    id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Build Artifact
# ---------------------------------------------------------------------------


class BuildArtifactBase(BaseSchema):
    artifact_id: str
    name: str
    artifact_type: str
    version: str | None = None
    digest: str | None = None
    registry_url: str | None = None
    build_system: str | None = None
    build_url: str | None = None
    has_sbom: bool = False
    has_provenance: bool = False
    has_signature: bool = False
    critical_vulns: int = 0
    high_vulns: int = 0
    release_id: uuid.UUID | None = None


class BuildArtifactCreate(BuildArtifactBase):
    pass


class BuildArtifactRead(BuildArtifactBase):
    id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# SBOM Record
# ---------------------------------------------------------------------------


class SBOMRecordBase(BaseSchema):
    sbom_id: str
    format: str
    spec_version: str | None = None
    component_count: int = 0
    artifact_id: uuid.UUID | None = None
    component_id: uuid.UUID | None = None


class SBOMRecordCreate(SBOMRecordBase):
    raw_content: dict | None = None


class SBOMRecordRead(SBOMRecordBase):
    id: uuid.UUID
    ingested_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------


class ReleaseBase(BaseSchema):
    release_id: str
    name: str
    version: str
    description: str | None = None
    status: ReleaseStatus = ReleaseStatus.DRAFT
    component_id: uuid.UUID | None = None
    target_env: str | None = None
    release_date: datetime | None = None


class ReleaseCreate(ReleaseBase):
    pass


class ReleaseRead(ReleaseBase):
    id: uuid.UUID
    compliance_score: float | None = None
    policy_evaluation: dict | None = None
    created_at: datetime
    updated_at: datetime


class ReleaseDetail(ReleaseRead):
    requirements: list["RequirementRead"] = []
    evidence_items: list["EvidenceItemRead"] = []
    artifacts: list["BuildArtifactRead"] = []
    exceptions: list["ExceptionRecordRead"] = []


# ---------------------------------------------------------------------------
# Policy Rule
# ---------------------------------------------------------------------------


class PolicyRuleBase(BaseSchema):
    rule_id: str
    name: str
    description: str | None = None
    category: str | None = None
    severity: SeverityLevel = SeverityLevel.HIGH
    enabled: bool = True
    blocking: bool = True
    rule_config: dict | None = None


class PolicyRuleCreate(PolicyRuleBase):
    pass


class PolicyRuleRead(PolicyRuleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Policy Evaluation Result
# ---------------------------------------------------------------------------


class PolicyCheckResult(BaseSchema):
    rule_id: str
    rule_name: str
    passed: bool
    blocking: bool
    severity: str
    message: str
    details: dict | None = None


class PolicyEvaluationResult(BaseSchema):
    release_id: str
    overall_passed: bool
    blocking_failures: int
    total_checks: int
    compliance_score: float
    checks: list[PolicyCheckResult]
    evaluated_at: datetime


# ---------------------------------------------------------------------------
# Incident
# ---------------------------------------------------------------------------


class IncidentBase(BaseSchema):
    incident_id: str
    title: str
    description: str | None = None
    severity: SeverityLevel
    status: IncidentStatus = IncidentStatus.OPEN
    affected_component_id: uuid.UUID | None = None
    affected_control_id: uuid.UUID | None = None
    resolved_at: datetime | None = None


class IncidentCreate(IncidentBase):
    pass


class IncidentRead(IncidentBase):
    id: uuid.UUID
    detected_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Exception Record
# ---------------------------------------------------------------------------


class ExceptionRecordBase(BaseSchema):
    exception_id: str
    title: str
    justification: str | None = None
    status: ExceptionStatus = ExceptionStatus.OPEN
    risk_acceptance_notes: str | None = None
    approver: str | None = None
    incident_id: uuid.UUID | None = None
    release_id: uuid.UUID | None = None
    affected_control_id: uuid.UUID | None = None
    expires_at: datetime | None = None


class ExceptionRecordCreate(ExceptionRecordBase):
    pass


class ExceptionRecordRead(ExceptionRecordBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Audit Bundle
# ---------------------------------------------------------------------------


class AuditBundleBase(BaseSchema):
    bundle_id: str
    title: str
    generated_by: str | None = None
    framework: str | None = None
    release_id: uuid.UUID | None = None


class AuditBundleCreate(AuditBundleBase):
    pass


class AuditBundleRead(AuditBundleBase):
    id: uuid.UUID
    generated_at: datetime
    content: dict | None = None


# ---------------------------------------------------------------------------
# Traceability
# ---------------------------------------------------------------------------


class TraceabilityNode(BaseSchema):
    node_id: str
    node_type: str  # requirement, control, evidence, test, release, artifact
    label: str
    status: str | None = None
    metadata: dict[str, Any] | None = None


class TraceabilityEdge(BaseSchema):
    source: str
    target: str
    relationship: str  # satisfies, tested_by, evidenced_by, implements, releases


class TraceabilityGraph(BaseSchema):
    nodes: list[TraceabilityNode]
    edges: list[TraceabilityEdge]
    requirement_id: str | None = None
    control_id: str | None = None
    release_id: str | None = None


# ---------------------------------------------------------------------------
# Dashboard Summary
# ---------------------------------------------------------------------------


class DashboardSummary(BaseSchema):
    total_requirements: int
    requirements_with_controls: int
    requirements_with_tests: int
    total_controls: int
    controls_implemented: int
    controls_with_evidence: int
    total_evidence_items: int
    evidence_valid: int
    evidence_expired: int
    total_releases: int
    releases_approved: int
    releases_blocked: int
    open_exceptions: int
    open_incidents: int
    compliance_score: float
    audit_completeness_score: float


# Rebuild models that have forward references
RequirementDetail.model_rebuild()
ControlDetail.model_rebuild()
ReleaseDetail.model_rebuild()
