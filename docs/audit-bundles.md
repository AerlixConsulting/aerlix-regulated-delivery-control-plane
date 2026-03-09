# Audit Bundle Guide

## What Is an Audit Bundle?

An audit bundle is a point-in-time snapshot of your compliance posture,
packaged for review by auditors, compliance teams, or authorizing officials.

## Bundle Contents

| Section | Description |
|---------|-------------|
| `bundle_metadata` | Bundle ID, framework, generator, timestamp |
| `control_summary` | All controls, implementation status, counts |
| `evidence_index` | All evidence items by type and status |
| `traceability_matrix` | Requirements → controls → tests |
| `release_readiness` | Release policy evaluation result |
| `gaps` | Untested reqs, controls without evidence, missing SBOMs |
| `exception_register` | All risk exceptions with approval and expiry |
| `incident_summary` | All incidents with severity and status |

## Generating a Bundle

### Via API

```bash
# JSON bundle
curl -X POST "http://localhost:8000/api/v1/audit/generate?format=json&release_id=REL-001" \
  -o audit-bundle.json

# Markdown bundle
curl -X POST "http://localhost:8000/api/v1/audit/generate?format=markdown&release_id=REL-001" \
  -o audit-bundle.md
```

### Via CLI

```bash
aerlix generate-audit-bundle --release-id REL-001 --output /tmp/audit.json
aerlix generate-audit-bundle --release-id REL-001 --format markdown --output /tmp/audit.md
```

### Via Dashboard

Navigate to **Audit Export** → select format and optional release ID → click **Download Audit Bundle**.

## Bundle ID

Each bundle is assigned a deterministic ID based on the release ID and generation timestamp:

```
BUNDLE-{sha256[:12].upper()}
```

This allows bundles to be referenced in audit trails.

## Example Bundle Structure

See `examples/audit-bundle.json` for a complete example.
