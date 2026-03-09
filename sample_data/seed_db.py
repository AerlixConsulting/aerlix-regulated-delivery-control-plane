"""Demo database seeder.

Seeds the control plane with a realistic regulated payments API scenario:
  - 2 system components (PaymentsAPI, AuthService)
  - 8 NIST 800-53 controls
  - 12 requirements
  - 15 evidence items
  - 5 test cases
  - 2 releases (one approved, one blocked)
  - 2 artifacts
  - 1 open exception
  - 1 incident
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db import AsyncSessionLocal, init_db
from app.models import (
    BuildArtifact,
    Control,
    ControlImplementation,
    ControlStatus,
    Deployment,
    EvidenceItem,
    EvidenceStatus,
    EvidenceType,
    ExceptionRecord,
    ExceptionStatus,
    Incident,
    IncidentStatus,
    Owner,
    PolicyRule,
    Release,
    ReleaseStatus,
    Requirement,
    RequirementStatus,
    RequirementType,
    SBOMRecord,
    SeverityLevel,
    SystemComponent,
    TestCase,
    release_evidence_link,
    release_requirement_link,
    requirement_control_link,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

OWNERS = [
    {
        "name": "Alice Chen",
        "email": "alice.chen@example.com",
        "role": "Security Engineer",
        "team": "Platform Security",
    },
    {
        "name": "Bob Okonkwo",
        "email": "bob.okonkwo@example.com",
        "role": "Compliance Lead",
        "team": "GRC",
    },
    {
        "name": "Carmen Rodriguez",
        "email": "carmen.rodriguez@example.com",
        "role": "Software Engineer",
        "team": "Payments Platform",
    },
]

COMPONENTS = [
    {
        "name": "PaymentsAPI",
        "component_type": "service",
        "description": "Regulated payments processing REST API. Handles PCI-DSS-relevant transaction flows.",
        "version": "2.4.1",
    },
    {
        "name": "AuthService",
        "component_type": "service",
        "description": "Authentication and authorization microservice. Issues JWT tokens.",
        "version": "1.8.0",
    },
    {
        "name": "AuditDB",
        "component_type": "database",
        "description": "Immutable audit log database (PostgreSQL with row-level security).",
        "version": "16.2",
    },
]

CONTROLS = [
    {
        "control_id": "AC-2",
        "family": "Access Control",
        "title": "Account Management",
        "description": "Manage information system accounts including establishing, activating, modifying, "
        "reviewing, disabling, and removing accounts.",
        "baseline": "low",
    },
    {
        "control_id": "AC-3",
        "family": "Access Control",
        "title": "Access Enforcement",
        "description": "Enforce approved authorizations for logical access to information and system resources.",
        "baseline": "low",
    },
    {
        "control_id": "AU-6",
        "family": "Audit and Accountability",
        "title": "Audit Record Review, Analysis, and Reporting",
        "description": "Review and analyze information system audit records for indications of inappropriate or "
        "unusual activity.",
        "baseline": "low",
    },
    {
        "control_id": "CA-7",
        "family": "Assessment, Authorization, and Monitoring",
        "title": "Continuous Monitoring",
        "description": "Develop a continuous monitoring strategy and implement a continuous monitoring program.",
        "baseline": "low",
    },
    {
        "control_id": "CM-3",
        "family": "Configuration Management",
        "title": "Configuration Change Control",
        "description": "Determine the types of changes to the information system that are configuration-controlled.",
        "baseline": "moderate",
    },
    {
        "control_id": "RA-5",
        "family": "Risk Assessment",
        "title": "Vulnerability Monitoring and Scanning",
        "description": "Monitor and scan for vulnerabilities in the information system and hosted applications.",
        "baseline": "moderate",
    },
    {
        "control_id": "SI-2",
        "family": "System and Information Integrity",
        "title": "Flaw Remediation",
        "description": "Identify, report, and correct information system flaws; install security-relevant "
        "software updates within defined time periods.",
        "baseline": "low",
    },
    {
        "control_id": "SA-10",
        "family": "System and Services Acquisition",
        "title": "Developer Configuration Management",
        "description": "Require the developer of the information system to perform configuration management "
        "during system development, implementation, and operation.",
        "baseline": "moderate",
    },
]

REQUIREMENTS = [
    {
        "req_id": "REQ-001",
        "title": "All API endpoints must require authentication",
        "description": "Every REST endpoint exposed by PaymentsAPI must validate a signed JWT token.",
        "req_type": RequirementType.SECURITY,
        "status": RequirementStatus.VERIFIED,
        "priority": "critical",
        "source": "PCI-DSS 8.2",
        "control_ids": ["AC-2", "AC-3"],
    },
    {
        "req_id": "REQ-002",
        "title": "All transactions must be logged to the audit database",
        "description": "PaymentsAPI must write a structured audit record for every transaction attempt.",
        "req_type": RequirementType.REGULATORY,
        "status": RequirementStatus.IMPLEMENTED,
        "priority": "critical",
        "source": "PCI-DSS 10.2",
        "control_ids": ["AU-6"],
    },
    {
        "req_id": "REQ-003",
        "title": "Dependency vulnerabilities must be scanned before release",
        "description": "All third-party dependencies must be scanned for known CVEs prior to production release.",
        "req_type": RequirementType.SECURITY,
        "status": RequirementStatus.VERIFIED,
        "priority": "high",
        "source": "NIST-800-53 RA-5",
        "control_ids": ["RA-5"],
    },
    {
        "req_id": "REQ-004",
        "title": "Infrastructure changes must follow change control process",
        "description": "All changes to production infrastructure must go through the CAB approval process.",
        "req_type": RequirementType.REGULATORY,
        "status": RequirementStatus.APPROVED,
        "priority": "high",
        "source": "NIST-800-53 CM-3",
        "control_ids": ["CM-3"],
    },
    {
        "req_id": "REQ-005",
        "title": "Security patches must be applied within SLA",
        "description": "Critical security patches must be applied within 7 days; high within 30 days.",
        "req_type": RequirementType.SECURITY,
        "status": RequirementStatus.IMPLEMENTED,
        "priority": "critical",
        "source": "FedRAMP SI-2",
        "control_ids": ["SI-2"],
    },
    {
        "req_id": "REQ-006",
        "title": "All container images must include an SBOM",
        "description": "Every container image published to the registry must have an attached CycloneDX SBOM.",
        "req_type": RequirementType.SECURITY,
        "status": RequirementStatus.IMPLEMENTED,
        "priority": "high",
        "source": "EO 14028 §4(e)",
        "control_ids": ["SA-10"],
    },
    {
        "req_id": "REQ-007",
        "title": "User accounts must be reviewed quarterly",
        "description": "A quarterly review of all system accounts must be conducted and documented.",
        "req_type": RequirementType.REGULATORY,
        "status": RequirementStatus.APPROVED,
        "priority": "medium",
        "source": "NIST-800-53 AC-2",
        "control_ids": ["AC-2"],
    },
    {
        "req_id": "REQ-008",
        "title": "Continuous monitoring must be in place",
        "description": "Automated monitoring dashboards must report security posture in near-real-time.",
        "req_type": RequirementType.SECURITY,
        "status": RequirementStatus.IMPLEMENTED,
        "priority": "high",
        "source": "FedRAMP CA-7",
        "control_ids": ["CA-7"],
    },
    {
        "req_id": "REQ-009",
        "title": "Build provenance must be recorded for all releases",
        "description": "SLSA provenance attestations must be generated and stored for every release artifact.",
        "req_type": RequirementType.SECURITY,
        "status": RequirementStatus.DRAFT,
        "priority": "high",
        "source": "SLSA Level 2",
        "control_ids": ["SA-10"],
    },
    {
        "req_id": "REQ-010",
        "title": "Secret scanning must be enabled on all repositories",
        "description": "GitHub Advanced Security secret scanning must be active on all source repositories.",
        "req_type": RequirementType.SECURITY,
        "status": RequirementStatus.IMPLEMENTED,
        "priority": "medium",
        "source": "Internal Policy SEC-12",
        "control_ids": ["CA-7"],
    },
    {
        "req_id": "REQ-011",
        "title": "API rate limiting must be enforced",
        "description": "All public-facing API endpoints must enforce rate limiting to prevent abuse.",
        "req_type": RequirementType.SYSTEM,
        "status": RequirementStatus.IMPLEMENTED,
        "priority": "medium",
        "source": "Architecture RFC-2023-04",
        "control_ids": ["AC-3"],
    },
    {
        "req_id": "REQ-012",
        "title": "Encryption at rest must be enabled for all data stores",
        "description": "All data at rest in production must use AES-256 encryption.",
        "req_type": RequirementType.SECURITY,
        "status": RequirementStatus.VERIFIED,
        "priority": "critical",
        "source": "PCI-DSS 3.4",
        "control_ids": ["AC-3"],
    },
]

EVIDENCE = [
    {
        "evidence_id": "EV-001",
        "title": "GitHub Actions CI run — PaymentsAPI v2.4.1 unit tests",
        "evidence_type": EvidenceType.CI_RUN,
        "status": EvidenceStatus.VALID,
        "source_system": "GitHub Actions",
        "source_url": "https://github.com/example/payments-api/actions/runs/123456",
        "control_id": "AU-6",
        "days_ago": 5,
    },
    {
        "evidence_id": "EV-002",
        "title": "Trivy dependency scan — PaymentsAPI v2.4.1",
        "evidence_type": EvidenceType.DEPENDENCY_SCAN,
        "status": EvidenceStatus.VALID,
        "source_system": "Trivy / GitHub Actions",
        "source_url": "https://github.com/example/payments-api/security/vulnerability-alerts",
        "control_id": "RA-5",
        "days_ago": 5,
    },
    {
        "evidence_id": "EV-003",
        "title": "Bandit SAST scan — PaymentsAPI v2.4.1",
        "evidence_type": EvidenceType.STATIC_ANALYSIS,
        "status": EvidenceStatus.VALID,
        "source_system": "Bandit / GitHub Actions",
        "source_url": "https://github.com/example/payments-api/actions/runs/123457",
        "control_id": "RA-5",
        "days_ago": 5,
    },
    {
        "evidence_id": "EV-004",
        "title": "Terraform IaC scan — production infrastructure",
        "evidence_type": EvidenceType.IAC_SCAN,
        "status": EvidenceStatus.VALID,
        "source_system": "Checkov",
        "control_id": "CM-3",
        "days_ago": 14,
    },
    {
        "evidence_id": "EV-005",
        "title": "Production deployment log — PaymentsAPI v2.3.0",
        "evidence_type": EvidenceType.DEPLOYMENT_LOG,
        "status": EvidenceStatus.VALID,
        "source_system": "ArgoCD",
        "control_id": "CM-3",
        "days_ago": 45,
    },
    {
        "evidence_id": "EV-006",
        "title": "Quarterly access review — Q4 2025",
        "evidence_type": EvidenceType.MANUAL_UPLOAD,
        "status": EvidenceStatus.VALID,
        "source_system": "GRC Platform",
        "control_id": "AC-2",
        "days_ago": 60,
    },
    {
        "evidence_id": "EV-007",
        "title": "Penetration test report — PaymentsAPI — Oct 2025",
        "evidence_type": EvidenceType.MANUAL_UPLOAD,
        "status": EvidenceStatus.VALID,
        "source_system": "External Security Firm",
        "control_id": "RA-5",
        "days_ago": 95,
    },
    {
        "evidence_id": "EV-008",
        "title": "SIEM alert monitoring proof — CloudWatch",
        "evidence_type": EvidenceType.AUDIT_LOG,
        "status": EvidenceStatus.VALID,
        "source_system": "AWS CloudWatch",
        "control_id": "CA-7",
        "days_ago": 3,
    },
    {
        "evidence_id": "EV-009",
        "title": "Unit test results — PaymentsAPI v2.4.1 — 247 passed",
        "evidence_type": EvidenceType.TEST_RESULT,
        "status": EvidenceStatus.VALID,
        "source_system": "pytest / GitHub Actions",
        "control_id": "SI-2",
        "days_ago": 5,
    },
    {
        "evidence_id": "EV-010",
        "title": "Integration test results — PaymentsAPI v2.4.1",
        "evidence_type": EvidenceType.TEST_RESULT,
        "status": EvidenceStatus.VALID,
        "source_system": "pytest / GitHub Actions",
        "control_id": "AU-6",
        "days_ago": 5,
    },
    {
        "evidence_id": "EV-011",
        "title": "Trivy scan — BlockedPaymentsAPI v2.5.0-rc1 (critical CVEs found)",
        "evidence_type": EvidenceType.DEPENDENCY_SCAN,
        "status": EvidenceStatus.REJECTED,
        "source_system": "Trivy / GitHub Actions",
        "control_id": "RA-5",
        "days_ago": 2,
    },
    {
        "evidence_id": "EV-012",
        "title": "SBOM — PaymentsAPI v2.4.1 (CycloneDX)",
        "evidence_type": EvidenceType.MANUAL_UPLOAD,
        "status": EvidenceStatus.VALID,
        "source_system": "Syft / GitHub Actions",
        "control_id": "SA-10",
        "days_ago": 5,
    },
    {
        "evidence_id": "EV-013",
        "title": "Secret scanning results — no secrets detected",
        "evidence_type": EvidenceType.STATIC_ANALYSIS,
        "status": EvidenceStatus.VALID,
        "source_system": "GitHub Advanced Security",
        "control_id": "CA-7",
        "days_ago": 5,
    },
    {
        "evidence_id": "EV-014",
        "title": "Flaw remediation ticket closure — CVE-2024-1234 patched",
        "evidence_type": EvidenceType.MANUAL_UPLOAD,
        "status": EvidenceStatus.VALID,
        "source_system": "Jira",
        "control_id": "SI-2",
        "days_ago": 20,
    },
    {
        "evidence_id": "EV-015",
        "title": "Access enforcement audit log export — 90 day window",
        "evidence_type": EvidenceType.AUDIT_LOG,
        "status": EvidenceStatus.EXPIRED,
        "source_system": "Splunk",
        "control_id": "AC-3",
        "days_ago": 100,
    },
]

TEST_CASES = [
    {
        "test_id": "TC-001",
        "name": "test_authentication_required",
        "description": "Verifies that unauthenticated requests to /v1/payments return 401.",
        "test_type": "integration",
        "req_id": "REQ-001",
        "last_result": "pass",
        "days_ago": 5,
    },
    {
        "test_id": "TC-002",
        "name": "test_audit_log_written_on_transaction",
        "description": "Asserts that every payment creates an immutable audit log entry.",
        "test_type": "integration",
        "req_id": "REQ-002",
        "last_result": "pass",
        "days_ago": 5,
    },
    {
        "test_id": "TC-003",
        "name": "test_rate_limiting_enforced",
        "description": "Verifies 429 response after exceeding rate limit threshold.",
        "test_type": "integration",
        "req_id": "REQ-011",
        "last_result": "pass",
        "days_ago": 5,
    },
    {
        "test_id": "TC-004",
        "name": "test_encryption_at_rest_enabled",
        "description": "Checks that RDS instance has encryption-at-rest enabled via AWS Config.",
        "test_type": "security",
        "req_id": "REQ-012",
        "last_result": "pass",
        "days_ago": 5,
    },
    {
        "test_id": "TC-005",
        "name": "test_dependency_scan_clean",
        "description": "Verifies Trivy scan returns no critical CVEs.",
        "test_type": "security",
        "req_id": "REQ-003",
        "last_result": "fail",  # blocked release scenario
        "days_ago": 2,
    },
]


# ---------------------------------------------------------------------------
# Seeder function
# ---------------------------------------------------------------------------


async def seed(force: bool = False) -> None:
    """Seed demo data into the database."""
    await init_db()
    logger.info("Starting demo data seed...")

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing = await db.execute(select(Requirement).limit(1))
        if existing.scalar_one_or_none() and not force:
            logger.info("Demo data already present. Use force=True to re-seed.")
            return

        # ----- Owners -----
        owners: dict[str, Owner] = {}
        for o in OWNERS:
            existing = await db.execute(select(Owner).where(Owner.email == o["email"]))
            owner = existing.scalar_one_or_none()
            if not owner:
                owner = Owner(**o)
                db.add(owner)
                await db.flush()
            owners[o["name"]] = owner

        # ----- System Components -----
        components: dict[str, SystemComponent] = {}
        for i, c in enumerate(COMPONENTS):
            existing = await db.execute(
                select(SystemComponent).where(SystemComponent.name == c["name"])
            )
            comp = existing.scalar_one_or_none()
            if not comp:
                owner = list(owners.values())[i % len(owners)]
                comp = SystemComponent(**c, owner_id=owner.id)
                db.add(comp)
                await db.flush()
            components[c["name"]] = comp

        # ----- Controls -----
        controls: dict[str, Control] = {}
        for c in CONTROLS:
            existing = await db.execute(
                select(Control).where(Control.control_id == c["control_id"])
            )
            ctrl = existing.scalar_one_or_none()
            if not ctrl:
                ctrl = Control(**c)
                db.add(ctrl)
                await db.flush()
            controls[c["control_id"]] = ctrl

        # Control implementations for PaymentsAPI
        payments_comp = components["PaymentsAPI"]
        impl_status_map = {
            "AC-2": ControlStatus.IMPLEMENTED,
            "AC-3": ControlStatus.IMPLEMENTED,
            "AU-6": ControlStatus.IMPLEMENTED,
            "CA-7": ControlStatus.IMPLEMENTED,
            "CM-3": ControlStatus.IMPLEMENTED,
            "RA-5": ControlStatus.IMPLEMENTED,
            "SI-2": ControlStatus.IMPLEMENTED,
            "SA-10": ControlStatus.PARTIALLY_IMPLEMENTED,
        }
        for ctrl_id, impl_status in impl_status_map.items():
            ctrl = controls[ctrl_id]
            existing = await db.execute(
                select(ControlImplementation).where(
                    ControlImplementation.control_id == ctrl.id,
                    ControlImplementation.component_id == payments_comp.id,
                )
            )
            if not existing.scalar_one_or_none():
                impl = ControlImplementation(
                    control_id=ctrl.id,
                    component_id=payments_comp.id,
                    status=impl_status,
                    responsible_role="Platform Security Team",
                    implementation_notes="Implemented via platform controls. See evidence EV-001 through EV-015.",
                )
                db.add(impl)
        await db.flush()

        # ----- Evidence Items -----
        evidence_map: dict[str, EvidenceItem] = {}
        for e in EVIDENCE:
            existing = await db.execute(
                select(EvidenceItem).where(EvidenceItem.evidence_id == e["evidence_id"])
            )
            ev_item = existing.scalar_one_or_none()
            if not ev_item:
                ctrl_id_str = e.pop("control_id", None)
                days_ago = e.pop("days_ago", 0)
                ctrl_obj = controls.get(ctrl_id_str) if ctrl_id_str else None
                ev_item = EvidenceItem(
                    **e,
                    control_id=ctrl_obj.id if ctrl_obj else None,
                    collected_at=datetime.now(UTC) - timedelta(days=days_ago),
                )
                db.add(ev_item)
                await db.flush()
            evidence_map[e["evidence_id"]] = ev_item

        # ----- Test Cases -----
        test_map: dict[str, TestCase] = {}
        for t in TEST_CASES:
            existing = await db.execute(select(TestCase).where(TestCase.test_id == t["test_id"]))
            tc = existing.scalar_one_or_none()
            if not tc:
                req_id_str = t.pop("req_id")
                days_ago = t.pop("days_ago", 0)
                tc = TestCase(
                    **t,
                    last_run_at=datetime.now(UTC) - timedelta(days=days_ago),
                )
                db.add(tc)
                await db.flush()
            test_map[t["test_id"]] = tc

        # ----- Requirements -----
        req_map: dict[str, Requirement] = {}
        for r in REQUIREMENTS:
            existing = await db.execute(
                select(Requirement).where(Requirement.req_id == r["req_id"])
            )
            req = existing.scalar_one_or_none()
            if not req:
                ctrl_ids = r.pop("control_ids", [])
                req = Requirement(
                    **r,
                    owner_id=list(owners.values())[0].id,
                )
                db.add(req)
                await db.flush()

                # Link to controls
                for ctrl_id_str in ctrl_ids:
                    ctrl = controls.get(ctrl_id_str)
                    if ctrl:
                        await db.execute(
                            requirement_control_link.insert()
                            .values(requirement_id=req.id, control_id=ctrl.id)
                            .prefix_with("ON CONFLICT DO NOTHING")
                        )
            req_map[r["req_id"]] = req

        # Assign test cases to requirements
        tc_req_mapping = {
            "TC-001": "REQ-001",
            "TC-002": "REQ-002",
            "TC-003": "REQ-011",
            "TC-004": "REQ-012",
            "TC-005": "REQ-003",
        }
        for tc_id, req_id_str in tc_req_mapping.items():
            tc = test_map.get(tc_id)
            req = req_map.get(req_id_str)
            if tc and req and tc.requirement_id is None:
                tc.requirement_id = req.id

        await db.flush()

        # ----- Build Artifacts -----
        # Artifact 1: Approved release artifact
        existing = await db.execute(
            select(BuildArtifact).where(BuildArtifact.artifact_id == "ART-001")
        )
        art1 = existing.scalar_one_or_none()
        if not art1:
            art1 = BuildArtifact(
                artifact_id="ART-001",
                name="payments-api",
                artifact_type="container",
                version="2.4.1",
                digest="sha256:a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
                registry_url="ghcr.io/example/payments-api:2.4.1",
                build_system="GitHub Actions",
                has_sbom=True,
                has_provenance=True,
                has_signature=True,
                critical_vulns=0,
                high_vulns=1,
            )
            db.add(art1)
            await db.flush()

        # Artifact 2: Blocked release artifact (has critical vulns, no SBOM)
        existing = await db.execute(
            select(BuildArtifact).where(BuildArtifact.artifact_id == "ART-002")
        )
        art2 = existing.scalar_one_or_none()
        if not art2:
            art2 = BuildArtifact(
                artifact_id="ART-002",
                name="payments-api",
                artifact_type="container",
                version="2.5.0-rc1",
                digest="sha256:b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
                registry_url="ghcr.io/example/payments-api:2.5.0-rc1",
                build_system="GitHub Actions",
                has_sbom=False,
                has_provenance=False,
                has_signature=False,
                critical_vulns=3,
                high_vulns=7,
            )
            db.add(art2)
            await db.flush()

        # SBOM for art1
        existing = await db.execute(select(SBOMRecord).where(SBOMRecord.sbom_id == "SBOM-001"))
        if not existing.scalar_one_or_none():
            sbom = SBOMRecord(
                sbom_id="SBOM-001",
                format="cyclonedx",
                spec_version="1.6",
                component_count=127,
                artifact_id=art1.id,
                component_id=components["PaymentsAPI"].id,
            )
            db.add(sbom)

        # ----- Releases -----

        # Release 1: Approved (compliant)
        existing = await db.execute(select(Release).where(Release.release_id == "REL-001"))
        rel1 = existing.scalar_one_or_none()
        if not rel1:
            rel1 = Release(
                release_id="REL-001",
                name="PaymentsAPI v2.4.1 — Production Release",
                version="2.4.1",
                description="Quarterly production release. Includes security patch for CVE-2024-1234 and rate limiting improvements.",
                status=ReleaseStatus.APPROVED,
                component_id=components["PaymentsAPI"].id,
                compliance_score=92.5,
                target_env="production",
                release_date=datetime.now(UTC) - timedelta(days=3),
            )
            db.add(rel1)
            await db.flush()
            art1.release_id = rel1.id

            # Link requirements
            for req_id_str in [
                "REQ-001",
                "REQ-002",
                "REQ-003",
                "REQ-005",
                "REQ-006",
                "REQ-011",
                "REQ-012",
            ]:
                req = req_map.get(req_id_str)
                if req:
                    await db.execute(
                        release_requirement_link.insert()
                        .values(release_id=rel1.id, requirement_id=req.id)
                        .prefix_with("ON CONFLICT DO NOTHING")
                    )

            # Link evidence
            for ev_id in [
                "EV-001",
                "EV-002",
                "EV-003",
                "EV-004",
                "EV-008",
                "EV-009",
                "EV-010",
                "EV-012",
            ]:
                ev = evidence_map.get(ev_id)
                if ev:
                    await db.execute(
                        release_evidence_link.insert()
                        .values(release_id=rel1.id, evidence_id=ev.id)
                        .prefix_with("ON CONFLICT DO NOTHING")
                    )

        # Deployment for REL-001
        existing = await db.execute(select(Deployment).where(Deployment.release_id == rel1.id))
        if not existing.scalar_one_or_none():
            dep = Deployment(
                release_id=rel1.id,
                environment="production",
                deployed_by="alice.chen@example.com",
                deployment_url="https://argocd.example.com/applications/payments-api",
                success=True,
                notes="Deployed via GitOps pipeline. All health checks passed.",
            )
            db.add(dep)

        # Release 2: Blocked (non-compliant)
        existing = await db.execute(select(Release).where(Release.release_id == "REL-002"))
        rel2 = existing.scalar_one_or_none()
        if not rel2:
            rel2 = Release(
                release_id="REL-002",
                name="PaymentsAPI v2.5.0-rc1 — Release Candidate",
                version="2.5.0-rc1",
                description="RC for v2.5.0. Blocked due to critical CVEs and missing SBOM.",
                status=ReleaseStatus.BLOCKED,
                component_id=components["PaymentsAPI"].id,
                compliance_score=44.4,
                target_env="staging",
                policy_evaluation={
                    "overall_passed": False,
                    "blocking_failures": 4,
                    "total_checks": 9,
                    "compliance_score": 44.4,
                },
            )
            db.add(rel2)
            await db.flush()
            art2.release_id = rel2.id

            # Link a few requirements
            for req_id_str in ["REQ-001", "REQ-003", "REQ-006"]:
                req = req_map.get(req_id_str)
                if req:
                    await db.execute(
                        release_requirement_link.insert()
                        .values(release_id=rel2.id, requirement_id=req.id)
                        .prefix_with("ON CONFLICT DO NOTHING")
                    )

        # ----- Incidents -----
        existing = await db.execute(select(Incident).where(Incident.incident_id == "INC-001"))
        incident = existing.scalar_one_or_none()
        if not incident:
            incident = Incident(
                incident_id="INC-001",
                title="Log4Shell exposure identified in legacy dependency",
                description="CVE-2021-44228 identified in a transitive dependency of AuthService. Mitigated via WAF rule.",
                severity=SeverityLevel.CRITICAL,
                status=IncidentStatus.CONTAINED,
                affected_component_id=components["AuthService"].id,
                affected_control_id=controls["SI-2"].id,
                detected_at=datetime.now(UTC) - timedelta(days=30),
            )
            db.add(incident)
            await db.flush()

        # ----- Exceptions -----
        existing = await db.execute(
            select(ExceptionRecord).where(ExceptionRecord.exception_id == "EXC-001")
        )
        if not existing.scalar_one_or_none():
            exc = ExceptionRecord(
                exception_id="EXC-001",
                title="Penetration test older than 90 days",
                justification=(
                    "Quarterly pentest is scheduled. WAF and IDS controls provide compensating coverage. "
                    "Exception approved pending the Q1 2026 pentest completion."
                ),
                status=ExceptionStatus.APPROVED,
                risk_acceptance_notes="CISO approved. Compensating controls documented.",
                approver="CISO — Jane Smith",
                incident_id=incident.id,
                affected_control_id=controls["RA-5"].id,
                expires_at=datetime.now(UTC) + timedelta(days=45),
            )
            db.add(exc)

        # ----- Policy Rules -----
        policy_rules = [
            {
                "rule_id": "RULE-001",
                "name": "All artifacts must have an SBOM",
                "category": "supply-chain",
                "severity": SeverityLevel.CRITICAL,
                "blocking": True,
            },
            {
                "rule_id": "RULE-002",
                "name": "No critical vulnerabilities",
                "category": "vulnerability-management",
                "severity": SeverityLevel.CRITICAL,
                "blocking": True,
            },
            {
                "rule_id": "RULE-003",
                "name": "All artifacts must have provenance",
                "category": "supply-chain",
                "severity": SeverityLevel.HIGH,
                "blocking": True,
            },
        ]
        for pr in policy_rules:
            existing = await db.execute(
                select(PolicyRule).where(PolicyRule.rule_id == pr["rule_id"])
            )
            if not existing.scalar_one_or_none():
                rule = PolicyRule(**pr)
                db.add(rule)

        await db.commit()
        logger.info("✅ Demo data seeded successfully.")
        print(
            "✅ Demo data seeded: 3 owners, 3 components, 8 controls, 12 requirements, "
            "15 evidence items, 5 test cases, 2 releases, 1 incident, 1 exception."
        )


if __name__ == "__main__":
    asyncio.run(seed())
