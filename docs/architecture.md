# Architecture Guide

## Overview

The Aerlix Regulated Delivery Control Plane is a multi-layer platform with:

1. **Data Layer** — PostgreSQL with async SQLAlchemy ORM
2. **Service Layer** — Python engines for traceability, policy evaluation, and audit export
3. **API Layer** — FastAPI REST API with Pydantic schemas
4. **Presentation Layer** — React/TypeScript dashboard + Typer CLI
5. **Async Workers** — Celery + Redis for background evidence ingestion

## Service Components

### API Server (FastAPI)
- Async Python 3.12 + FastAPI 0.111
- All database interactions are async (asyncpg driver)
- OpenAPI docs at `/docs`
- CORS enabled for localhost development

### Traceability Engine (NetworkX)
- Directed graph linking all entities
- Nodes: Requirements, Controls, Evidence, Tests, Releases, Artifacts
- Edges: satisfies, tested_by, evidenced_by, includes, contains
- Methods: forward/backward trace, gap detection, coverage stats

### Policy Engine
- Loads rules from YAML policy files
- Evaluates rules against a ReleaseContext object
- Returns PolicyEvaluationResult with per-check pass/fail and compliance score
- Supported conditions: artifact_has_sbom, no_critical_vulns, controls_implemented, etc.

### Audit Exporter
- Assembles data from all entities into a structured bundle
- Produces JSON (machine-readable) and Markdown (human-readable) output
- Includes: control summary, evidence index, traceability matrix, gap analysis, exception register

## Data Flow

```
CI/CD Pipeline
    |
    v
Evidence Ingestor
    |
    v
EvidenceItem (DB) ---> Control ---> Requirement ---> Release
                                                         |
                                                    Policy Engine
                                                         |
                                               PolicyEvaluationResult
                                                         |
                                                    Audit Exporter
                                                         |
                                               audit-bundle.json / .md
```

## Trust Boundaries

- All API endpoints are internal-facing (no auth in demo; JWT auth available via config)
- Evidence items include SHA-256 content hashes for tamper detection
- Audit bundles include generation metadata (timestamp, generator identity)

## Technology Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI 0.111, Python 3.12 |
| ORM | SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 |
| Graph | NetworkX 3.3 |
| CLI | Typer |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Queue | Celery + Redis |
| Containers | Docker, docker-compose |
| CI | GitHub Actions |
