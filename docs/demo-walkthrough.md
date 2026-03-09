# Demo Walkthrough

This walkthrough takes approximately 10 minutes and demonstrates the full
platform end-to-end using the seeded "regulated payments API" scenario.

## Setup

```bash
git clone https://github.com/AerlixConsulting/aerlix-regulated-delivery-control-plane.git
cd aerlix-regulated-delivery-control-plane
cp .env.example .env
docker compose up -d
# Wait ~10 seconds for services to start
docker compose exec api python -m sample_data.seed_db
```

## Step 1: Visit the Dashboard

Open http://localhost:3000

You will see:
- Compliance posture score rings
- 8 controls, 12 requirements, 15 evidence items
- 2 releases (1 approved, 1 blocked)
- 1 open exception

## Step 2: Explore Requirements Traceability

Click **Requirements** in the sidebar.

Observe:
- REQ-009 (build provenance) is in DRAFT status — not yet implemented
- Some requirements may show "no tests" or "no controls" gap indicators

Click **Traceability** to see coverage percentages for:
- Requirement → Control mapping
- Requirement → Test coverage
- Control → Evidence coverage

## Step 3: Review Controls and Evidence

Click **Controls & Evidence**.

You'll see 8 NIST 800-53 controls grouped by family with evidence coverage indicators.

## Step 4: Inspect Supply Chain

Click **Supply Chain**.

Compare the two artifacts:
- ART-001 (PaymentsAPI 2.4.1): has SBOM, provenance, signature, 0 critical CVEs → APPROVED
- ART-002 (PaymentsAPI 2.5.0-rc1): missing SBOM, provenance, signature, 3 critical CVEs → BLOCKED

## Step 5: Evaluate Release Policy

Click **Release Gates**.

Click **Evaluate** on REL-001 (v2.4.1):
- You should see APPROVED with 88.9%+ compliance score
- RULE-007 (evidence freshness) may warn about one older evidence item

Click **Evaluate** on REL-002 (v2.5.0-rc1):
- You should see BLOCKED with 4 blocking failures:
  - RULE-001: No SBOM
  - RULE-002: No provenance
  - RULE-003: 3 critical vulnerabilities
  - RULE-008: Test TC-005 failed

## Step 6: Generate an Audit Bundle

Click **Audit Export**.

Enter `REL-001` in the Release ID field, select JSON format, click **Download Audit Bundle**.

Open the downloaded file to see the full audit package.

Alternatively via CLI:
```bash
aerlix generate-audit-bundle --release-id REL-001 --output /tmp/audit.json
cat /tmp/audit.json | python -m json.tool | head -80
```

## Step 7: CLI Traceability

```bash
# Install in local virtualenv
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql+asyncpg://aerlix:aerlix_dev_password@localhost:5432/aerlix_control_plane"

# Show traceability from REQ-001
aerlix trace show --requirement REQ-001

# Show traceability from AC-2 (Access Control)
aerlix trace show --control AC-2

# Export full graph
aerlix graph-export --output /tmp/graph.json
wc -l /tmp/graph.json
```

## What the Demo Proves

After completing this walkthrough, you can answer:

- Which controls are satisfied by REL-001? (AC-2, AC-3, AU-6, CA-7, CM-3, RA-5, SI-2)
- Why is REL-002 blocked? (Missing SBOM, critical CVEs, failed test)
- What evidence supports AC-2? (EV-006: Quarterly access review)
- What exceptions exist? (EXC-001: Pentest age exception, approved, expires Q1 2026)
- What is the audit completeness score? (Calculated live from control implementation and evidence status)
