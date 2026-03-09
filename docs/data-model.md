# Data Model

## Core Entities

### Owner
Person or team responsible for requirements and system components.
Fields: name, email, role, team

### SystemComponent
A deployable service, library, database, or infrastructure component.
Fields: name, component_type, description, version, owner_id

### Requirement
A business, system, security, privacy, or regulatory requirement.
Fields: req_id (e.g. REQ-001), title, description, req_type, status, priority, source, owner_id, parent_id
Many-to-many with Control via requirement_control_link.

### Control
A NIST 800-53 control or similar framework control.
Fields: control_id (e.g. AC-2), family, title, description, framework, baseline

### ControlImplementation
Implementation record linking a Control to a SystemComponent.
Fields: control_id, component_id, status, implementation_notes, responsible_role, inherited_from, last_assessed

### EvidenceItem
A piece of compliance evidence collected from a system, tool, or manual upload.
Fields: evidence_id, title, evidence_type, status, source_system, source_url, content_hash, collected_at, expires_at, metadata, control_id

### TestCase
A test case linked to a requirement.
Fields: test_id, name, description, test_type, requirement_id, last_result, last_run_at

### BuildArtifact
A versioned build artifact (container, package, binary).
Fields: artifact_id, name, artifact_type, version, digest, registry_url, build_system, build_url, has_sbom, has_provenance, has_signature, critical_vulns, high_vulns, release_id

### SBOMRecord
An SBOM (CycloneDX or SPDX) attached to a build artifact.
Fields: sbom_id, format, spec_version, component_count, artifact_id, component_id, raw_content

### ProvenanceRecord
A SLSA-style provenance record for a build artifact.
Fields: artifact_id, build_invocation_id, builder_id, source_repo, source_commit, slsa_level, verified, raw_content

### Release
A versioned release of a system component.
Fields: release_id, name, version, description, status, component_id, policy_evaluation, compliance_score, target_env, release_date
Many-to-many with Requirement and EvidenceItem.

### Deployment
A deployment record for a release to an environment.
Fields: release_id, environment, deployed_at, deployed_by, deployment_url, success, notes

### PolicyRule
A configurable policy rule for release gating.
Fields: rule_id, name, description, category, severity, enabled, blocking, rule_config

### Incident
A security or operational incident.
Fields: incident_id, title, description, severity, status, affected_component_id, affected_control_id, detected_at, resolved_at

### ExceptionRecord
A documented risk exception with approval and expiry.
Fields: exception_id, title, justification, status, risk_acceptance_notes, approver, incident_id, release_id, affected_control_id, expires_at

### AuditBundle
A generated audit package.
Fields: bundle_id, title, generated_by, framework, release_id, content, generated_at

## Key Relationships

- Requirement -> Control (M:M via requirement_control_link)
- Release -> Requirement (M:M via release_requirement_link)
- Release -> EvidenceItem (M:M via release_evidence_link)
- Release -> BuildArtifact (1:M)
- Control -> EvidenceItem (1:M)
- Requirement -> TestCase (1:M)
- BuildArtifact -> SBOMRecord (1:M)
- BuildArtifact -> ProvenanceRecord (1:M)
- Incident -> ExceptionRecord (1:M)
