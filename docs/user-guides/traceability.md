# Traceability Graph

The traceability engine builds a directed graph connecting requirements → controls → evidence → releases, enabling gap analysis and audit trail generation.

## Concepts

```
Requirement → Control → Evidence
     ↓            ↓         ↓
  TestCase    TestCase    Artifact
     ↓
  Release → Artifact
```

## Graph Node Types

| Node Type | ID Pattern | Description |
|-----------|-----------|-------------|
| `requirement` | `REQ-NNN` | Business, system, or regulatory requirements |
| `control` | `AC-N`, `CM-N`, etc. | NIST 800-53 controls |
| `evidence` | `EV-NNN` | CI artifacts, scan results, audit logs |
| `test_case` | `TC-NNN` | Unit/integration test results |
| `release` | `REL-NNN` | Software release candidates |
| `artifact` | `ART-NNN` | Container images, binaries |

## Edge (Relationship) Types

| Edge | Source → Target | Meaning |
|------|----------------|---------|
| `satisfies` | requirement → control | Requirement maps to control |
| `verified_by` | requirement → test | Requirement verified by test |
| `supported_by` | control → evidence | Control supported by evidence |
| `includes` | release → requirement | Release includes requirement |
| `contains` | release → artifact | Release packages artifact |

## API Endpoints

### Get Full Graph

```bash
GET /api/v1/traceability/graph
```

### Get Subgraph from Root

```bash
GET /api/v1/traceability/graph?root_id=REQ-001
```

### Get Coverage Statistics

```bash
GET /api/v1/traceability/coverage
```

Example response:

```json
{
  "total_requirements": 12,
  "total_controls": 8,
  "req_control_coverage_pct": 91.7,
  "req_test_coverage_pct": 83.3,
  "control_evidence_coverage_pct": 100.0,
  "untested_requirements": 2,
  "unmapped_requirements": 1,
  "controls_without_evidence": 0
}
```

## CLI Commands

```bash
# Show full traceability graph
aerlix trace show

# Show subgraph rooted at a requirement
aerlix trace show --requirement REQ-001

# Show subgraph rooted at a control
aerlix trace show --control AC-2

# Export graph as JSON
aerlix graph-export --output /tmp/graph.json
```

## Gap Analysis

The engine highlights:

- **Untested requirements** — requirements with no linked test cases
- **Unmapped requirements** — requirements with no linked controls
- **Controls without evidence** — controls not backed by any evidence item
