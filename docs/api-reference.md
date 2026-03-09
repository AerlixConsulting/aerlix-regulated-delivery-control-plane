# API Reference

All endpoints are prefixed with `/api/v1`. Interactive docs available at `http://localhost:8000/docs`.

## Requirements

| Method | Path | Description |
|--------|------|-------------|
| GET | `/requirements` | List requirements (filter by status, req_type) |
| GET | `/requirements/count` | Count all requirements |
| GET | `/requirements/{req_id}` | Get requirement with controls and test cases |
| POST | `/requirements` | Create requirement |
| PUT | `/requirements/{req_id}` | Update requirement |
| DELETE | `/requirements/{req_id}` | Delete requirement |

## Controls

| Method | Path | Description |
|--------|------|-------------|
| GET | `/controls` | List controls (filter by family, baseline) |
| GET | `/controls/{control_id}` | Get control with implementations and evidence |
| POST | `/controls` | Create control |
| PUT | `/controls/{control_id}` | Update control |
| DELETE | `/controls/{control_id}` | Delete control |
| GET | `/controls/{control_id}/implementations` | List implementations |
| POST | `/controls/{control_id}/implementations` | Add implementation |

## Evidence

| Method | Path | Description |
|--------|------|-------------|
| GET | `/evidence` | List evidence items (filter by type, status) |
| GET | `/evidence/{evidence_id}` | Get evidence item |
| POST | `/evidence` | Ingest evidence item |
| PUT | `/evidence/{evidence_id}` | Update evidence item |
| DELETE | `/evidence/{evidence_id}` | Delete evidence item |

## Releases

| Method | Path | Description |
|--------|------|-------------|
| GET | `/releases` | List releases (filter by status) |
| GET | `/releases/{release_id}` | Get release with requirements, evidence, artifacts |
| POST | `/releases` | Create release |
| PUT | `/releases/{release_id}` | Update release |
| DELETE | `/releases/{release_id}` | Delete release |

## Traceability

| Method | Path | Description |
|--------|------|-------------|
| GET | `/traceability/graph` | Full traceability graph (nodes + edges) |
| GET | `/traceability/graph/requirement/{req_id}` | Subgraph for requirement |
| GET | `/traceability/graph/control/{control_id}` | Subgraph for control |
| GET | `/traceability/graph/release/{release_id}` | Subgraph for release |
| GET | `/traceability/gaps` | Gap analysis |
| GET | `/traceability/stats` | Coverage statistics |

## Policies

| Method | Path | Description |
|--------|------|-------------|
| GET | `/policies/rules` | List default policy rules |
| POST | `/policies/evaluate/{release_id}` | Evaluate release against all rules |

## Audit

| Method | Path | Description |
|--------|------|-------------|
| POST | `/audit/generate` | Generate and download audit bundle |
| GET | `/audit/bundles` | List generated audit bundles |
| GET | `/audit/summary` | Audit readiness summary |

## System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API info |
