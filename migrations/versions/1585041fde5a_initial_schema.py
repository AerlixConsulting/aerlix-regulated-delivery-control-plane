"""initial_schema

Revision ID: 1585041fde5a
Revises:
Create Date: 2026-03-09 19:52:27.989260

NOTE: This migration was scaffolded from the ORM models. Run
  alembic revision --autogenerate -m "initial_schema"
against a live PostgreSQL instance to regenerate with exact column
types and constraints.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1585041fde5a"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # owners
    op.create_table(
        "owners",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200)),
        sa.Column("role", sa.String(100)),
        sa.Column("team", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # system_components
    op.create_table(
        "system_components",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False, unique=True),
        sa.Column("component_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("version", sa.String(100)),
        sa.Column("owner_id", sa.UUID(as_uuid=True), sa.ForeignKey("owners.id")),
        sa.Column("metadata", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # controls
    op.create_table(
        "controls",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("control_id", sa.String(100), nullable=False, unique=True),
        sa.Column("family", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("framework", sa.String(100)),
        sa.Column("baseline", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # requirements
    op.create_table(
        "requirements",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("req_id", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "req_type",
            sa.Enum(
                "business", "system", "security", "privacy", "regulatory", name="requirementtype"
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "approved",
                "implemented",
                "verified",
                "deprecated",
                name="requirementstatus",
            ),
            nullable=False,
        ),
        sa.Column("priority", sa.String(50)),
        sa.Column("source", sa.String(200)),
        sa.Column("owner_id", sa.UUID(as_uuid=True), sa.ForeignKey("owners.id")),
        sa.Column("parent_id", sa.UUID(as_uuid=True), sa.ForeignKey("requirements.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # requirement_control_link
    op.create_table(
        "requirement_control_link",
        sa.Column(
            "requirement_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("requirements.id"),
            primary_key=True,
        ),
        sa.Column(
            "control_id", sa.UUID(as_uuid=True), sa.ForeignKey("controls.id"), primary_key=True
        ),
    )

    # control_implementations
    op.create_table(
        "control_implementations",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "control_id", sa.UUID(as_uuid=True), sa.ForeignKey("controls.id"), nullable=False
        ),
        sa.Column("component_id", sa.UUID(as_uuid=True), sa.ForeignKey("system_components.id")),
        sa.Column(
            "status",
            sa.Enum(
                "not_implemented",
                "planned",
                "partially_implemented",
                "implemented",
                "inherited",
                "not_applicable",
                name="controlstatus",
            ),
            nullable=False,
        ),
        sa.Column("implementation_notes", sa.Text()),
        sa.Column("responsible_role", sa.String(200)),
        sa.Column("inherited_from", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # evidence_items
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("evidence_id", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column(
            "evidence_type",
            sa.Enum(
                "ci_run",
                "test_result",
                "static_analysis",
                "dependency_scan",
                "iac_scan",
                "deployment_log",
                "manual_upload",
                "audit_log",
                name="evidencetype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "valid", "expired", "rejected", name="evidencestatus"),
            nullable=False,
        ),
        sa.Column("source_system", sa.String(200)),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("content_hash", sa.String(256)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", sa.JSON()),
        sa.Column("control_id", sa.UUID(as_uuid=True), sa.ForeignKey("controls.id")),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # test_cases
    op.create_table(
        "test_cases",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("test_type", sa.String(100)),
        sa.Column("last_result", sa.String(50)),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("requirement_id", sa.UUID(as_uuid=True), sa.ForeignKey("requirements.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # releases
    op.create_table(
        "releases",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("release_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("version", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "candidate",
                "blocked",
                "approved",
                "deployed",
                "rolled_back",
                name="releasestatus",
            ),
            nullable=False,
        ),
        sa.Column("component_id", sa.UUID(as_uuid=True), sa.ForeignKey("system_components.id")),
        sa.Column("policy_evaluation", sa.JSON()),
        sa.Column("compliance_score", sa.Float()),
        sa.Column("target_env", sa.String(100)),
        sa.Column("release_date", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # release_requirement_link
    op.create_table(
        "release_requirement_link",
        sa.Column(
            "release_id", sa.UUID(as_uuid=True), sa.ForeignKey("releases.id"), primary_key=True
        ),
        sa.Column(
            "requirement_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("requirements.id"),
            primary_key=True,
        ),
    )

    # release_evidence_link
    op.create_table(
        "release_evidence_link",
        sa.Column(
            "release_id", sa.UUID(as_uuid=True), sa.ForeignKey("releases.id"), primary_key=True
        ),
        sa.Column(
            "evidence_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("evidence_items.id"),
            primary_key=True,
        ),
    )

    # build_artifacts
    op.create_table(
        "build_artifacts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("artifact_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("version", sa.String(100)),
        sa.Column("artifact_type", sa.String(100)),
        sa.Column("has_sbom", sa.Boolean(), default=False),
        sa.Column("has_provenance", sa.Boolean(), default=False),
        sa.Column("has_signature", sa.Boolean(), default=False),
        sa.Column("critical_vulns", sa.Integer(), default=0),
        sa.Column("high_vulns", sa.Integer(), default=0),
        sa.Column("release_id", sa.UUID(as_uuid=True), sa.ForeignKey("releases.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # sbom_records
    op.create_table(
        "sbom_records",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("sbom_id", sa.String(100), nullable=False, unique=True),
        sa.Column("format", sa.String(50), nullable=False),
        sa.Column("spec_version", sa.String(20)),
        sa.Column("component_count", sa.Integer(), default=0),
        sa.Column("artifact_id", sa.UUID(as_uuid=True), sa.ForeignKey("build_artifacts.id")),
        sa.Column("component_id", sa.UUID(as_uuid=True), sa.ForeignKey("system_components.id")),
        sa.Column("raw_content", sa.JSON()),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # provenance_records
    op.create_table(
        "provenance_records",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("build_artifacts.id"),
            nullable=False,
        ),
        sa.Column("build_invocation_id", sa.String(500)),
        sa.Column("builder_id", sa.String(500)),
        sa.Column("source_repo", sa.String(500)),
        sa.Column("source_commit", sa.String(64)),
        sa.Column("slsa_level", sa.Integer()),
        sa.Column("verified", sa.Boolean(), default=False),
        sa.Column("raw_content", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # deployments
    op.create_table(
        "deployments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "release_id", sa.UUID(as_uuid=True), sa.ForeignKey("releases.id"), nullable=False
        ),
        sa.Column("environment", sa.String(100)),
        sa.Column("deployed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deployed_by", sa.String(200)),
        sa.Column("deployment_url", sa.String(1000)),
        sa.Column("success", sa.Boolean(), default=True),
        sa.Column("notes", sa.Text()),
    )

    # policy_rules
    op.create_table(
        "policy_rules",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100)),
        sa.Column(
            "severity",
            sa.Enum("critical", "high", "medium", "low", "informational", name="severitylevel"),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), default=True),
        sa.Column("blocking", sa.Boolean(), default=True),
        sa.Column("rule_config", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # incidents
    op.create_table(
        "incidents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "severity",
            sa.Enum("critical", "high", "medium", "low", "informational", name="severitylevel"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "investigating", "resolved", "closed", name="incidentstatus"),
            nullable=False,
        ),
        sa.Column(
            "affected_component_id", sa.UUID(as_uuid=True), sa.ForeignKey("system_components.id")
        ),
        sa.Column("affected_control_id", sa.UUID(as_uuid=True), sa.ForeignKey("controls.id")),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # exception_records
    op.create_table(
        "exception_records",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("exception_id", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("justification", sa.Text()),
        sa.Column(
            "status",
            sa.Enum("open", "approved", "expired", "closed", name="exceptionstatus"),
            nullable=False,
        ),
        sa.Column("risk_acceptance_notes", sa.Text()),
        sa.Column("approver", sa.String(200)),
        sa.Column("incident_id", sa.UUID(as_uuid=True), sa.ForeignKey("incidents.id")),
        sa.Column("release_id", sa.UUID(as_uuid=True), sa.ForeignKey("releases.id")),
        sa.Column("affected_control_id", sa.UUID(as_uuid=True), sa.ForeignKey("controls.id")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # audit_bundles
    op.create_table(
        "audit_bundles",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("bundle_id", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("generated_by", sa.String(200)),
        sa.Column("framework", sa.String(100)),
        sa.Column("release_id", sa.UUID(as_uuid=True), sa.ForeignKey("releases.id")),
        sa.Column("content", sa.JSON()),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_bundles")
    op.drop_table("exception_records")
    op.drop_table("incidents")
    op.drop_table("policy_rules")
    op.drop_table("deployments")
    op.drop_table("provenance_records")
    op.drop_table("sbom_records")
    op.drop_table("build_artifacts")
    op.drop_table("release_evidence_link")
    op.drop_table("release_requirement_link")
    op.drop_table("releases")
    op.drop_table("test_cases")
    op.drop_table("evidence_items")
    op.drop_table("control_implementations")
    op.drop_table("requirement_control_link")
    op.drop_table("requirements")
    op.drop_table("controls")
    op.drop_table("system_components")
    op.drop_table("owners")
    op.execute("DROP TYPE IF EXISTS requirementtype")
    op.execute("DROP TYPE IF EXISTS requirementstatus")
    op.execute("DROP TYPE IF EXISTS controlstatus")
    op.execute("DROP TYPE IF EXISTS evidencetype")
    op.execute("DROP TYPE IF EXISTS evidencestatus")
    op.execute("DROP TYPE IF EXISTS releasestatus")
    op.execute("DROP TYPE IF EXISTS severitylevel")
    op.execute("DROP TYPE IF EXISTS incidentstatus")
    op.execute("DROP TYPE IF EXISTS exceptionstatus")
