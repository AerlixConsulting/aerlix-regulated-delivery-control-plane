# Policy Engine Guide

## Overview

The policy engine evaluates a set of configurable rules against a release before it can be approved.
Rules are defined in YAML and evaluated against a `ReleaseContext` containing all relevant release data.

## Policy File Schema

```yaml
rules:
  - id: RULE-001              # Unique rule identifier
    name: "Rule name"         # Human-readable name
    description: "..."        # Optional description
    category: supply-chain    # Grouping category
    severity: critical        # critical, high, medium, low
    blocking: true            # If true, failure blocks the release
    enabled: true             # Can be disabled without removing
    condition:
      type: artifact_has_sbom # Condition type (see below)
      threshold: 1.0          # Condition-specific parameters
```

## Supported Condition Types

| Condition Type | Parameters | Description |
|----------------|------------|-------------|
| `artifact_has_sbom` | `threshold` (0.0–1.0) | Fraction of artifacts requiring SBOM |
| `artifact_has_provenance` | `threshold` | Fraction requiring SLSA provenance |
| `artifact_has_signature` | `threshold` | Fraction requiring digital signature |
| `no_critical_vulns` | `max_allowed` (int) | Max permitted critical CVEs |
| `no_high_vulns_above_threshold` | `max_allowed` (int) | Max permitted high CVEs |
| `controls_implemented` | `required_controls` (list) | Controls that must be implemented |
| `required_approvals_present` | `required_approvers` (list) | Required approver identities |
| `no_open_blocking_exceptions` | — | No open risk exceptions permitted |
| `evidence_freshness_days` | `max_age_days` (int) | Max evidence age in days |
| `test_pass_rate` | `min_pass_rate` (0.0–1.0) | Minimum test pass rate |
| `always_pass` | — | Informational rule, always passes |

## Default Policy Rules

The default ruleset (in `app/services/policy_engine.py`) includes 9 rules:

1. RULE-001: All artifacts must have SBOM (blocking, critical)
2. RULE-002: All artifacts must have provenance (blocking, high)
3. RULE-003: No critical vulnerabilities (blocking, critical)
4. RULE-004: High vulnerabilities below threshold of 3 (blocking, high)
5. RULE-005: Required NIST controls implemented (blocking, critical)
6. RULE-006: No open blocking exceptions (blocking, high)
7. RULE-007: Evidence freshness within 90 days (non-blocking, medium)
8. RULE-008: Test pass rate 100% (blocking, high)
9. RULE-009: Artifacts must be signed (non-blocking, medium)

## Compliance Score

The compliance score is calculated as:

```
score = (passed_checks / total_checks) * 100
```

A release passes if all **blocking** rules pass.
Non-blocking failures reduce the score but do not block release.

## Example Evaluation Output

```json
{
  "release_id": "REL-001",
  "overall_passed": true,
  "blocking_failures": 0,
  "total_checks": 9,
  "compliance_score": 88.9,
  "checks": [
    {
      "rule_id": "RULE-001",
      "rule_name": "All artifacts must have an SBOM",
      "passed": true,
      "blocking": true,
      "severity": "critical",
      "message": "1/1 artifacts have SBOM (required: 100%)."
    }
  ]
}
```

## Using Custom Policy Files

```bash
# CLI
aerlix evaluate-release --release-id REL-001 --policy my-policy.yaml

# Python
from app.services.policy_engine import PolicyEngine, ReleaseContext

engine = PolicyEngine.from_yaml_file("my-policy.yaml")
ctx = ReleaseContext(release_id="REL-001", artifacts=[...])
result = engine.evaluate(ctx)
```
