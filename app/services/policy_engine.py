"""Policy engine: evaluates release readiness against configurable rules.

Rules are defined as YAML policy files with the following schema:
  rules:
    - id: RULE-001
      name: "SBOM Required"
      category: supply-chain
      severity: critical
      blocking: true
      condition:
        type: artifact_has_sbom
        threshold: 1.0   # 100% of artifacts must have SBOM

Supported condition types:
  - artifact_has_sbom
  - artifact_has_provenance
  - artifact_has_signature
  - no_critical_vulns
  - no_high_vulns_above_threshold
  - controls_implemented
  - required_approvals_present
  - no_open_blocking_exceptions
  - evidence_freshness_days
  - test_pass_rate
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import yaml

from app.schemas import PolicyCheckResult, PolicyEvaluationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Policy rule model
# ---------------------------------------------------------------------------


@dataclass
class PolicyCondition:
    condition_type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyRule:
    rule_id: str
    name: str
    description: str = ""
    category: str = "general"
    severity: str = "high"
    blocking: bool = True
    enabled: bool = True
    condition: PolicyCondition = field(default_factory=lambda: PolicyCondition("always_pass"))


# ---------------------------------------------------------------------------
# Evaluation context
# ---------------------------------------------------------------------------


@dataclass
class ReleaseContext:
    """All data needed to evaluate policy rules against a release."""

    release_id: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    controls_implemented: list[str] = field(default_factory=list)
    required_controls: list[str] = field(default_factory=list)
    approvers: list[str] = field(default_factory=list)
    required_approvers: list[str] = field(default_factory=list)
    open_blocking_exceptions: list[dict[str, Any]] = field(default_factory=list)
    evidence_items: list[dict[str, Any]] = field(default_factory=list)
    test_results: list[dict[str, Any]] = field(default_factory=list)
    evidence_max_age_days: int = 90


# ---------------------------------------------------------------------------
# Policy Engine
# ---------------------------------------------------------------------------


class PolicyEngine:
    """Loads and evaluates policy rules against a release context."""

    def __init__(self, rules: list[PolicyRule] | None = None) -> None:
        self.rules: list[PolicyRule] = rules or []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, yaml_content: str) -> PolicyEngine:
        data = yaml.safe_load(yaml_content)
        rules = []
        for r in data.get("rules", []):
            cond_data = r.get("condition", {})
            condition = PolicyCondition(
                condition_type=cond_data.get("type", "always_pass"),
                params={k: v for k, v in cond_data.items() if k != "type"},
            )
            rules.append(
                PolicyRule(
                    rule_id=r["id"],
                    name=r["name"],
                    description=r.get("description", ""),
                    category=r.get("category", "general"),
                    severity=r.get("severity", "high"),
                    blocking=r.get("blocking", True),
                    enabled=r.get("enabled", True),
                    condition=condition,
                )
            )
        return cls(rules=rules)

    @classmethod
    def from_yaml_file(cls, path: str) -> PolicyEngine:
        with open(path) as f:
            return cls.from_yaml(f.read())

    def add_rule(self, rule: PolicyRule) -> None:
        self.rules.append(rule)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, context: ReleaseContext) -> PolicyEvaluationResult:
        checks: list[PolicyCheckResult] = []
        blocking_failures = 0

        for rule in self.rules:
            if not rule.enabled:
                continue
            check = self._evaluate_rule(rule, context)
            checks.append(check)
            if not check.passed and check.blocking:
                blocking_failures += 1

        total = len(checks)
        passed_count = sum(1 for c in checks if c.passed)
        score = round((passed_count / total) * 100, 1) if total else 100.0
        overall_passed = blocking_failures == 0

        return PolicyEvaluationResult(
            release_id=context.release_id,
            overall_passed=overall_passed,
            blocking_failures=blocking_failures,
            total_checks=total,
            compliance_score=score,
            checks=checks,
            evaluated_at=datetime.now(UTC),
        )

    def _evaluate_rule(self, rule: PolicyRule, ctx: ReleaseContext) -> PolicyCheckResult:
        ctype = rule.condition.condition_type
        params = rule.condition.params

        try:
            passed, message, details = self._check(ctype, params, ctx)
        except Exception as exc:
            logger.exception("Error evaluating rule %s", rule.rule_id)
            passed, message, details = False, f"Evaluation error: {exc}", None

        return PolicyCheckResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            passed=passed,
            blocking=rule.blocking,
            severity=rule.severity,
            message=message,
            details=details,
        )

    def _check(
        self,
        condition_type: str,
        params: dict[str, Any],
        ctx: ReleaseContext,
    ) -> tuple[bool, str, dict | None]:
        """Dispatch to the appropriate check implementation."""

        match condition_type:
            case "artifact_has_sbom":
                return self._check_artifact_sbom(ctx, params)
            case "artifact_has_provenance":
                return self._check_artifact_provenance(ctx, params)
            case "artifact_has_signature":
                return self._check_artifact_signature(ctx, params)
            case "no_critical_vulns":
                return self._check_no_critical_vulns(ctx, params)
            case "no_high_vulns_above_threshold":
                return self._check_high_vulns_threshold(ctx, params)
            case "controls_implemented":
                return self._check_controls_implemented(ctx, params)
            case "required_approvals_present":
                return self._check_approvals(ctx, params)
            case "no_open_blocking_exceptions":
                return self._check_exceptions(ctx, params)
            case "evidence_freshness_days":
                return self._check_evidence_freshness(ctx, params)
            case "test_pass_rate":
                return self._check_test_pass_rate(ctx, params)
            case "always_pass":
                return True, "Rule always passes (informational).", None
            case _:
                return False, f"Unknown condition type: {condition_type}", None

    # ------------------------------------------------------------------
    # Individual checkers
    # ------------------------------------------------------------------

    def _check_artifact_sbom(
        self, ctx: ReleaseContext, params: dict
    ) -> tuple[bool, str, dict | None]:
        threshold = float(params.get("threshold", 1.0))
        if not ctx.artifacts:
            return True, "No artifacts to check.", None
        with_sbom = sum(1 for a in ctx.artifacts if a.get("has_sbom"))
        ratio = with_sbom / len(ctx.artifacts)
        passed = ratio >= threshold
        return (
            passed,
            f"{with_sbom}/{len(ctx.artifacts)} artifacts have SBOM (required: {threshold * 100:.0f}%).",
            {"with_sbom": with_sbom, "total": len(ctx.artifacts), "ratio": ratio},
        )

    def _check_artifact_provenance(
        self, ctx: ReleaseContext, params: dict
    ) -> tuple[bool, str, dict | None]:
        threshold = float(params.get("threshold", 1.0))
        if not ctx.artifacts:
            return True, "No artifacts to check.", None
        with_prov = sum(1 for a in ctx.artifacts if a.get("has_provenance"))
        ratio = with_prov / len(ctx.artifacts)
        passed = ratio >= threshold
        return (
            passed,
            f"{with_prov}/{len(ctx.artifacts)} artifacts have provenance.",
            {"with_provenance": with_prov, "total": len(ctx.artifacts)},
        )

    def _check_artifact_signature(
        self, ctx: ReleaseContext, params: dict
    ) -> tuple[bool, str, dict | None]:
        threshold = float(params.get("threshold", 1.0))
        if not ctx.artifacts:
            return True, "No artifacts to check.", None
        with_sig = sum(1 for a in ctx.artifacts if a.get("has_signature"))
        ratio = with_sig / len(ctx.artifacts)
        passed = ratio >= threshold
        return (
            passed,
            f"{with_sig}/{len(ctx.artifacts)} artifacts are signed.",
            {"with_signature": with_sig, "total": len(ctx.artifacts)},
        )

    def _check_no_critical_vulns(
        self, ctx: ReleaseContext, params: dict
    ) -> tuple[bool, str, dict | None]:
        total_critical = sum(a.get("critical_vulns", 0) for a in ctx.artifacts)
        max_allowed = int(params.get("max_allowed", 0))
        passed = total_critical <= max_allowed
        return (
            passed,
            f"Total critical vulnerabilities: {total_critical} (max allowed: {max_allowed}).",
            {"critical_vulns": total_critical},
        )

    def _check_high_vulns_threshold(
        self, ctx: ReleaseContext, params: dict
    ) -> tuple[bool, str, dict | None]:
        total_high = sum(a.get("high_vulns", 0) for a in ctx.artifacts)
        max_allowed = int(params.get("max_allowed", 5))
        passed = total_high <= max_allowed
        return (
            passed,
            f"Total high vulnerabilities: {total_high} (max allowed: {max_allowed}).",
            {"high_vulns": total_high},
        )

    def _check_controls_implemented(
        self, ctx: ReleaseContext, params: dict
    ) -> tuple[bool, str, dict | None]:
        required = set(params.get("required_controls", ctx.required_controls))
        implemented = set(ctx.controls_implemented)
        missing = required - implemented
        passed = len(missing) == 0
        return (
            passed,
            f"Missing control implementations: {sorted(missing) if missing else 'none'}.",
            {"missing": sorted(missing), "required": sorted(required)},
        )

    def _check_approvals(self, ctx: ReleaseContext, params: dict) -> tuple[bool, str, dict | None]:
        required = set(params.get("required_approvers", ctx.required_approvers))
        present = set(ctx.approvers)
        missing = required - present
        passed = len(missing) == 0
        return (
            passed,
            f"Missing required approvers: {sorted(missing) if missing else 'none'}.",
            {"missing": sorted(missing), "required": sorted(required)},
        )

    def _check_exceptions(self, ctx: ReleaseContext, params: dict) -> tuple[bool, str, dict | None]:
        open_exc = [e for e in ctx.open_blocking_exceptions if e.get("status") == "open"]
        passed = len(open_exc) == 0
        return (
            passed,
            f"{len(open_exc)} open blocking exception(s) found.",
            {"open_exceptions": [e.get("exception_id") for e in open_exc]},
        )

    def _check_evidence_freshness(
        self, ctx: ReleaseContext, params: dict
    ) -> tuple[bool, str, dict | None]:
        max_age_days = int(params.get("max_age_days", ctx.evidence_max_age_days))
        cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
        stale = []
        for ev in ctx.evidence_items:
            collected_at = ev.get("collected_at")
            if collected_at and isinstance(collected_at, datetime):
                if collected_at.tzinfo is None:
                    collected_at = collected_at.replace(tzinfo=UTC)
                if collected_at < cutoff:
                    stale.append(ev.get("evidence_id"))
        passed = len(stale) == 0
        return (
            passed,
            f"{len(stale)} evidence item(s) older than {max_age_days} days.",
            {"stale_evidence": stale, "max_age_days": max_age_days},
        )

    def _check_test_pass_rate(
        self, ctx: ReleaseContext, params: dict
    ) -> tuple[bool, str, dict | None]:
        min_pass_rate = float(params.get("min_pass_rate", 1.0))
        if not ctx.test_results:
            # If no tests registered, consider it a warning rather than block
            return True, "No test results recorded.", None
        passed_tests = sum(1 for t in ctx.test_results if t.get("result") == "pass")
        rate = passed_tests / len(ctx.test_results)
        passed = rate >= min_pass_rate
        return (
            passed,
            f"Test pass rate: {rate * 100:.1f}% (required: {min_pass_rate * 100:.0f}%).",
            {"passed_tests": passed_tests, "total_tests": len(ctx.test_results), "rate": rate},
        )


# ---------------------------------------------------------------------------
# Default ruleset for demo
# ---------------------------------------------------------------------------

DEFAULT_POLICY_YAML = """
rules:
  - id: RULE-001
    name: "All artifacts must have an SBOM"
    description: "Every build artifact included in a release must have an attached SBOM."
    category: supply-chain
    severity: critical
    blocking: true
    condition:
      type: artifact_has_sbom
      threshold: 1.0

  - id: RULE-002
    name: "All artifacts must have provenance"
    description: "Build provenance (SLSA) must be present for all artifacts."
    category: supply-chain
    severity: high
    blocking: true
    condition:
      type: artifact_has_provenance
      threshold: 1.0

  - id: RULE-003
    name: "No critical vulnerabilities"
    description: "Zero critical CVEs are permitted in any release artifact."
    category: vulnerability-management
    severity: critical
    blocking: true
    condition:
      type: no_critical_vulns
      max_allowed: 0

  - id: RULE-004
    name: "High vulnerabilities below threshold"
    description: "At most 3 high-severity CVEs permitted."
    category: vulnerability-management
    severity: high
    blocking: true
    condition:
      type: no_high_vulns_above_threshold
      max_allowed: 3

  - id: RULE-005
    name: "Required NIST-800-53 controls implemented"
    description: "All controls in the moderate baseline must be implemented or inherited."
    category: compliance
    severity: critical
    blocking: true
    condition:
      type: controls_implemented

  - id: RULE-006
    name: "No open blocking exceptions"
    description: "No unresolved blocking risk exceptions may remain open at release time."
    category: risk-management
    severity: high
    blocking: true
    condition:
      type: no_open_blocking_exceptions

  - id: RULE-007
    name: "Evidence freshness within 90 days"
    description: "All linked evidence must have been collected within the last 90 days."
    category: compliance
    severity: medium
    blocking: false
    condition:
      type: evidence_freshness_days
      max_age_days: 90

  - id: RULE-008
    name: "Test pass rate ≥ 100%"
    description: "All registered test cases for this release must pass."
    category: quality
    severity: high
    blocking: true
    condition:
      type: test_pass_rate
      min_pass_rate: 1.0

  - id: RULE-009
    name: "Artifacts must be signed"
    description: "All artifacts must carry a digital signature."
    category: supply-chain
    severity: medium
    blocking: false
    condition:
      type: artifact_has_signature
      threshold: 1.0
"""


def get_default_policy_engine() -> PolicyEngine:
    return PolicyEngine.from_yaml(DEFAULT_POLICY_YAML)
