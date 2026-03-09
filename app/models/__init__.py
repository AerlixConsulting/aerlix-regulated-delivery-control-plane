"""SQLAlchemy ORM models for the Aerlix Control Plane.

Entity hierarchy:
  SystemComponent → Service → Owner
  Requirement → Control → ControlImplementation
  EvidenceItem → TestCase → BuildArtifact
  SBOMRecord → ProvenanceRecord
  Release → Deployment
  Incident → ExceptionRecord
  PolicyRule → AuditBundle
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class RequirementStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"


class RequirementType(str, enum.Enum):
    BUSINESS = "business"
    SYSTEM = "system"
    SECURITY = "security"
    PRIVACY = "privacy"
    REGULATORY = "regulatory"


class ControlStatus(str, enum.Enum):
    NOT_IMPLEMENTED = "not_implemented"
    PLANNED = "planned"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    IMPLEMENTED = "implemented"
    INHERITED = "inherited"
    NOT_APPLICABLE = "not_applicable"


class EvidenceType(str, enum.Enum):
    CI_RUN = "ci_run"
    TEST_RESULT = "test_result"
    STATIC_ANALYSIS = "static_analysis"
    DEPENDENCY_SCAN = "dependency_scan"
    IAC_SCAN = "iac_scan"
    DEPLOYMENT_LOG = "deployment_log"
    MANUAL_UPLOAD = "manual_upload"
    AUDIT_LOG = "audit_log"


class EvidenceStatus(str, enum.Enum):
    PENDING = "pending"
    VALID = "valid"
    EXPIRED = "expired"
    REJECTED = "rejected"


class ReleaseStatus(str, enum.Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    BLOCKED = "blocked"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"


class SeverityLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ExceptionStatus(str, enum.Enum):
    OPEN = "open"
    APPROVED = "approved"
    EXPIRED = "expired"
    REMEDIATED = "remediated"
    DENIED = "denied"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ---------------------------------------------------------------------------
# Association / link tables (many-to-many)
# ---------------------------------------------------------------------------

from sqlalchemy import Table  # noqa: E402

requirement_control_link = Table(
    "requirement_control_link",
    Base.metadata,
    Column("requirement_id", Uuid(as_uuid=True), ForeignKey("requirements.id"), primary_key=True),
    Column("control_id", Uuid(as_uuid=True), ForeignKey("controls.id"), primary_key=True),
)

release_requirement_link = Table(
    "release_requirement_link",
    Base.metadata,
    Column("release_id", Uuid(as_uuid=True), ForeignKey("releases.id"), primary_key=True),
    Column("requirement_id", Uuid(as_uuid=True), ForeignKey("requirements.id"), primary_key=True),
)

release_evidence_link = Table(
    "release_evidence_link",
    Base.metadata,
    Column("release_id", Uuid(as_uuid=True), ForeignKey("releases.id"), primary_key=True),
    Column("evidence_id", Uuid(as_uuid=True), ForeignKey("evidence_items.id"), primary_key=True),
)


# ---------------------------------------------------------------------------
# Owner / System / Service
# ---------------------------------------------------------------------------


class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(100))
    team: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    components: Mapped[list["SystemComponent"]] = relationship(back_populates="owner")
    requirements: Mapped[list["Requirement"]] = relationship(back_populates="owner")


class SystemComponent(Base):
    __tablename__ = "system_components"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    component_type: Mapped[str] = mapped_column(String(100))  # service, library, db, infra
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(String(50))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("owners.id"))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["Owner | None"] = relationship(back_populates="components")
    releases: Mapped[list["Release"]] = relationship(back_populates="component")
    sbom_records: Mapped[list["SBOMRecord"]] = relationship(back_populates="component")


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    req_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. REQ-001
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    req_type: Mapped[RequirementType] = mapped_column(
        Enum(RequirementType), default=RequirementType.SYSTEM
    )
    status: Mapped[RequirementStatus] = mapped_column(
        Enum(RequirementStatus), default=RequirementStatus.DRAFT
    )
    priority: Mapped[str | None] = mapped_column(String(20))  # critical, high, medium, low
    source: Mapped[str | None] = mapped_column(String(200))  # regulatory source / standard
    owner_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("owners.id"))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("requirements.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["Owner | None"] = relationship(back_populates="requirements")
    parent: Mapped["Requirement | None"] = relationship(
        back_populates="children", remote_side="Requirement.id"
    )
    children: Mapped[list["Requirement"]] = relationship(back_populates="parent")
    controls: Mapped[list["Control"]] = relationship(
        secondary=requirement_control_link, back_populates="requirements"
    )
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="requirement")
    releases: Mapped[list["Release"]] = relationship(
        secondary=release_requirement_link, back_populates="requirements"
    )

    @property
    def is_completed(self) -> bool:
        return self.status in {RequirementStatus.VERIFIED, RequirementStatus.DEPRECATED}


# ---------------------------------------------------------------------------
# Control
# ---------------------------------------------------------------------------


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    control_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. AC-2
    family: Mapped[str] = mapped_column(String(100))  # Access Control, Audit, etc.
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    framework: Mapped[str] = mapped_column(String(100), default="NIST-800-53-Rev5")
    baseline: Mapped[str | None] = mapped_column(String(50))  # low, moderate, high
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    requirements: Mapped[list["Requirement"]] = relationship(
        secondary=requirement_control_link, back_populates="controls"
    )
    implementations: Mapped[list["ControlImplementation"]] = relationship(back_populates="control")
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(back_populates="control")


class ControlImplementation(Base):
    __tablename__ = "control_implementations"
    __table_args__ = (UniqueConstraint("control_id", "component_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    control_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("controls.id"), nullable=False
    )
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("system_components.id")
    )
    status: Mapped[ControlStatus] = mapped_column(
        Enum(ControlStatus), default=ControlStatus.NOT_IMPLEMENTED
    )
    implementation_notes: Mapped[str | None] = mapped_column(Text)
    responsible_role: Mapped[str | None] = mapped_column(String(200))
    inherited_from: Mapped[str | None] = mapped_column(String(200))  # inherited provider name
    last_assessed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    control: Mapped["Control"] = relationship(back_populates="implementations")


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_type: Mapped[EvidenceType] = mapped_column(Enum(EvidenceType))
    status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus), default=EvidenceStatus.PENDING
    )
    source_system: Mapped[str | None] = mapped_column(String(200))  # GitHub Actions, Jenkins, etc.
    source_url: Mapped[str | None] = mapped_column(String(1000))
    content_hash: Mapped[str | None] = mapped_column(String(64))  # SHA-256
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)
    control_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("controls.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    control: Mapped["Control | None"] = relationship(back_populates="evidence_items")
    releases: Mapped[list["Release"]] = relationship(
        secondary=release_evidence_link, back_populates="evidence_items"
    )


# ---------------------------------------------------------------------------
# Test Case
# ---------------------------------------------------------------------------


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    test_type: Mapped[str | None] = mapped_column(String(100))  # unit, integration, e2e, security
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("requirements.id")
    )
    last_result: Mapped[str | None] = mapped_column(String(20))  # pass, fail, skip
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    requirement: Mapped["Requirement | None"] = relationship(back_populates="test_cases")


# ---------------------------------------------------------------------------
# Build Artifact / SBOM / Provenance
# ---------------------------------------------------------------------------


class BuildArtifact(Base):
    __tablename__ = "build_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(100))  # container, package, binary
    version: Mapped[str | None] = mapped_column(String(100))
    digest: Mapped[str | None] = mapped_column(String(100))  # sha256:...
    registry_url: Mapped[str | None] = mapped_column(String(1000))
    build_system: Mapped[str | None] = mapped_column(String(100))
    build_url: Mapped[str | None] = mapped_column(String(1000))
    has_sbom: Mapped[bool] = mapped_column(Boolean, default=False)
    has_provenance: Mapped[bool] = mapped_column(Boolean, default=False)
    has_signature: Mapped[bool] = mapped_column(Boolean, default=False)
    critical_vulns: Mapped[int] = mapped_column(Integer, default=0)
    high_vulns: Mapped[int] = mapped_column(Integer, default=0)
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("releases.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    release: Mapped["Release | None"] = relationship(back_populates="artifacts")
    sbom_records: Mapped[list["SBOMRecord"]] = relationship(back_populates="artifact")
    provenance_records: Mapped[list["ProvenanceRecord"]] = relationship(back_populates="artifact")


class SBOMRecord(Base):
    __tablename__ = "sbom_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sbom_id: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    format: Mapped[str] = mapped_column(String(50))  # cyclonedx, spdx
    spec_version: Mapped[str | None] = mapped_column(String(20))
    component_count: Mapped[int] = mapped_column(Integer, default=0)
    artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("build_artifacts.id")
    )
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("system_components.id")
    )
    raw_content: Mapped[dict | None] = mapped_column(JSON)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    artifact: Mapped["BuildArtifact | None"] = relationship(back_populates="sbom_records")
    component: Mapped["SystemComponent | None"] = relationship(back_populates="sbom_records")


class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("build_artifacts.id"), nullable=False
    )
    build_invocation_id: Mapped[str | None] = mapped_column(String(500))
    builder_id: Mapped[str | None] = mapped_column(String(500))
    source_repo: Mapped[str | None] = mapped_column(String(500))
    source_commit: Mapped[str | None] = mapped_column(String(64))
    slsa_level: Mapped[int | None] = mapped_column(Integer)  # 0–4
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_content: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    artifact: Mapped["BuildArtifact"] = relationship(back_populates="provenance_records")


# ---------------------------------------------------------------------------
# Release / Deployment
# ---------------------------------------------------------------------------


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    release_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReleaseStatus] = mapped_column(Enum(ReleaseStatus), default=ReleaseStatus.DRAFT)
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("system_components.id")
    )
    policy_evaluation: Mapped[dict | None] = mapped_column(JSON)  # last policy eval result
    compliance_score: Mapped[float | None] = mapped_column(Float)
    target_env: Mapped[str | None] = mapped_column(String(100))
    release_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    component: Mapped["SystemComponent | None"] = relationship(back_populates="releases")
    requirements: Mapped[list["Requirement"]] = relationship(
        secondary=release_requirement_link, back_populates="releases"
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        secondary=release_evidence_link, back_populates="releases"
    )
    artifacts: Mapped[list["BuildArtifact"]] = relationship(back_populates="release")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="release")
    exceptions: Mapped[list["ExceptionRecord"]] = relationship(back_populates="release")


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    release_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("releases.id"), nullable=False
    )
    environment: Mapped[str] = mapped_column(String(100))  # dev, staging, prod
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    deployed_by: Mapped[str | None] = mapped_column(String(200))
    deployment_url: Mapped[str | None] = mapped_column(String(1000))
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    release: Mapped["Release"] = relationship(back_populates="deployments")


# ---------------------------------------------------------------------------
# Policy Rule
# ---------------------------------------------------------------------------


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))  # supply-chain, compliance, etc.
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel), default=SeverityLevel.HIGH)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    blocking: Mapped[bool] = mapped_column(Boolean, default=True)
    rule_config: Mapped[dict | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# Incident / Exception
# ---------------------------------------------------------------------------


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel))
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.OPEN
    )
    affected_component_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("system_components.id")
    )
    affected_control_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("controls.id")
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    exceptions: Mapped[list["ExceptionRecord"]] = relationship(back_populates="incident")


class ExceptionRecord(Base):
    __tablename__ = "exception_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exception_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    justification: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ExceptionStatus] = mapped_column(
        Enum(ExceptionStatus), default=ExceptionStatus.OPEN
    )
    risk_acceptance_notes: Mapped[str | None] = mapped_column(Text)
    approver: Mapped[str | None] = mapped_column(String(200))
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("incidents.id")
    )
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("releases.id")
    )
    affected_control_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("controls.id")
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    incident: Mapped["Incident | None"] = relationship(back_populates="exceptions")
    release: Mapped["Release | None"] = relationship(back_populates="exceptions")


# ---------------------------------------------------------------------------
# Audit Bundle
# ---------------------------------------------------------------------------


class AuditBundle(Base):
    __tablename__ = "audit_bundles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bundle_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_by: Mapped[str | None] = mapped_column(String(200))
    framework: Mapped[str | None] = mapped_column(String(100))
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("releases.id")
    )
    content: Mapped[dict | None] = mapped_column(JSON)  # full bundle JSON
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
