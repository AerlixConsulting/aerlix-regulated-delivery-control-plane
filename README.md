# Aerlix Regulated Delivery Control Plane

<div align="center">

**A compliance-native software delivery control plane for regulated environments.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![NIST 800-53](https://img.shields.io/badge/NIST-800--53-red.svg)](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)

</div>

---

## What It Is

The **Aerlix Regulated Delivery Control Plane** is a reference implementation platform that connects every artifact in regulated software delivery — from business requirements to deployed containers — through a unified, traceable, audit-ready system.

It is designed for engineering teams and compliance officers operating in:

- FedRAMP-aligned environments
- NIST 800-53 controlled systems
- PCI-DSS, HIPAA, or SOC 2 regulated pipelines
- Continuous Authorization to Operate (cATO) programs

**The central question it answers is:** _"Can I prove, right now, that this release is compliant — and here is the evidence?"_

---

## What It Does

| Capability | Description |
|------------|-------------|
| **Requirements Traceability** | Ingest requirements from YAML, link to controls, tests, owners, and releases. Detect gaps. |
| **Control Mapping** | Model NIST 800-53 controls, map them to technical evidence, track implementation status. |
| **Evidence Collection** | Normalize CI/CD artifacts, scan results, deployment logs, and manual uploads into structured evidence. |
| **Supply Chain Integrity** | Ingest SBOMs (CycloneDX/SPDX), check provenance, flag artifacts missing signatures or attestations. |
| **Release Policy Gates** | Evaluate configurable YAML policy rules before every release. Block on critical failures. |
| **Audit Export** | Generate downloadable JSON and Markdown audit packages with a full evidence index and traceability matrix. |
| **Incident & Exception Linkage** | Attach incidents and risk exceptions to controls, systems, and releases. |
| **CLI & API** | Both a REST API (FastAPI) and a Python CLI (Typer) with rich terminal output. |

---

## Architecture Overview

```
+------------------------------------------------------------------+
|                      Aerlix Control Plane                         |
|                                                                    |
|  Requirements Traceability  Controls & Impls  Evidence Items      |
|          |                        |                 |             |
|          +------------------------+-----------------+             |
|                                   |                               |
|                         Traceability Engine (NetworkX)            |
|                                   |                               |
|              Release Gates <------+-------> Policy Engine         |
|                    |                        (YAML rules)          |
|              Audit Exporter (JSON + Markdown bundles)             |
|                                                                    |
|  REST API (FastAPI) | React Dashboard | Typer CLI                 |
+------------------------------------------------------------------+
```

---

## Quickstart (Under 5 Minutes)

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone and configure

```bash
git clone https://github.com/AerlixConsulting/aerlix-regulated-delivery-control-plane.git
cd aerlix-regulated-delivery-control-plane
cp .env.example .env
```

### 2. Start all services

```bash
make up
# or: docker compose up -d
```

### 3. Seed demo data

```bash
make seed-db
# or: docker compose exec api python -m sample_data.seed_db
```

### 4. Explore

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **pgAdmin** | http://localhost:5050 (admin@aerlix.io / admin) |

---

## Demo Walkthrough

After seeding, the demo includes two releases:

- `REL-001` — PaymentsAPI v2.4.1 — **Approved** (all policy checks pass)
- `REL-002` — PaymentsAPI v2.5.0-rc1 — **Blocked** (critical CVEs, missing SBOM)

```bash
# Evaluate release readiness
aerlix evaluate-release --release-id REL-001
aerlix evaluate-release --release-id REL-002

# Show traceability
aerlix trace show --requirement REQ-001
aerlix trace show --control AC-2

# Generate an audit bundle
aerlix generate-audit-bundle --release-id REL-001 --output /tmp/audit.json
```

---

## Repository Structure

```
aerlix-regulated-delivery-control-plane/
+-- app/                        # FastAPI backend
|   +-- api/v1/                 # REST endpoints
|   +-- core/config.py          # Configuration
|   +-- db.py                   # Async SQLAlchemy
|   +-- models/__init__.py      # ORM models (16 entities)
|   +-- schemas/__init__.py     # Pydantic schemas
|   +-- services/               # Traceability, Policy, Audit engines
|   +-- cli/main.py             # Typer CLI
|   \-- main.py                 # FastAPI application
+-- frontend/                   # React/TypeScript dashboard
+-- sample_data/seed_db.py      # Demo seeding script
+-- tests/                      # pytest test suite
+-- examples/                   # Sample YAML/JSON files
+-- docs/                       # Extended documentation
+-- Dockerfile                  # API container
+-- docker-compose.yml          # Full stack orchestration
+-- Makefile                    # Development commands
\-- .github/workflows/          # CI/CD pipelines
```

---

## CLI Commands

```bash
aerlix init-demo                              # Seed demo database
aerlix ingest-requirements FILE.yaml          # Ingest requirements
aerlix ingest-controls FILE.yaml              # Ingest controls
aerlix ingest-evidence FILE.json              # Ingest evidence items
aerlix evaluate-release --release-id REL-001  # Evaluate release policy
aerlix generate-audit-bundle --output out.json
aerlix trace show --requirement REQ-001
aerlix trace show --control AC-2
aerlix graph-export --output graph.json
```

---

## Policy Engine

Policy rules are defined in YAML and evaluated at release time:

```yaml
rules:
  - id: RULE-001
    name: "All artifacts must have an SBOM"
    category: supply-chain
    severity: critical
    blocking: true
    condition:
      type: artifact_has_sbom
      threshold: 1.0
```

See `examples/policy-rules.yaml` and `docs/policy-engine.md`.

---

## Documentation

| Document | Description |
|----------|-------------|
| `docs/architecture.md` | Service architecture and data flow |
| `docs/data-model.md` | Entity descriptions and relationships |
| `docs/policy-engine.md` | Policy rule schema and examples |
| `docs/audit-bundles.md` | Audit bundle generation |
| `docs/demo-walkthrough.md` | Step-by-step demo guide |
| `docs/roadmap.md` | Planned features |

---

## License

Apache 2.0 — see LICENSE.

---

**Aerlix Consulting** — Regulated software delivery, done right.
