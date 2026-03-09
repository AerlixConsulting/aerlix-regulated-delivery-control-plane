# Roadmap

## Current Capabilities (v0.1.0)

- Requirements traceability engine (NetworkX)
- NIST 800-53 control catalog and implementation tracking
- Evidence ingestion and normalization
- SBOM ingestion (CycloneDX)
- Release policy gate engine (configurable YAML rules)
- Audit bundle export (JSON + Markdown)
- Incident and exception register
- FastAPI REST API
- React dashboard (8 pages)
- Typer CLI
- Docker + docker-compose setup
- Demo data seeder

## Planned Features

### v0.2.0 — OSCAL Integration
- Export control implementations as OSCAL System Security Plan (SSP)
- Import OSCAL component definitions
- FedRAMP-specific baseline profiles

### v0.3.0 — SLSA Verification
- Verify SLSA provenance attestations in-band
- Cosign signature verification for container images
- SLSA level tracking per artifact

### v0.4.0 — Live GitHub Integration
- GitHub Actions webhook listener
- Automatic evidence ingestion from workflow runs
- Pull request traceability linking
- Branch protection policy enforcement

### v0.5.0 — SIEM Evidence Feeds
- Splunk evidence connector
- AWS CloudWatch evidence collector
- Azure Sentinel integration
- Evidence freshness auto-refresh

### v0.6.0 — Jira / ServiceNow Integration
- Import requirements from Jira epics
- Sync incidents from ServiceNow
- Exception workflow automation

### v1.0.0 — FedRAMP Package Support
- Complete FedRAMP High/Moderate baseline
- POA&M tracking
- Authorization boundary documentation
- Continuous monitoring dashboard for AOs

## Community Contributions Welcome

- Additional evidence connectors
- Policy rule templates for specific frameworks (PCI-DSS, HIPAA, ISO 27001)
- Graph visualization improvements
- Additional export formats (XCCDF, STIX)
