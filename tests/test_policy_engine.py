"""Tests for the PolicyEngine."""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.policy_engine import (
    PolicyCondition,
    PolicyEngine,
    PolicyRule,
    ReleaseContext,
    get_default_policy_engine,
)


def make_rule(
    rule_id: str,
    condition_type: str,
    blocking: bool = True,
    severity: str = "high",
    **params,
) -> PolicyRule:
    return PolicyRule(
        rule_id=rule_id,
        name=f"Rule {rule_id}",
        blocking=blocking,
        severity=severity,
        condition=PolicyCondition(condition_type=condition_type, params=params),
    )


class TestPolicyEngineArtifactChecks:
    def test_sbom_required_passes_when_all_have_sbom(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "artifact_has_sbom", threshold=1.0)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[
                {"artifact_id": "A1", "has_sbom": True},
                {"artifact_id": "A2", "has_sbom": True},
            ],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed
        assert result.checks[0].passed

    def test_sbom_required_fails_when_missing(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "artifact_has_sbom", threshold=1.0)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[
                {"artifact_id": "A1", "has_sbom": True},
                {"artifact_id": "A2", "has_sbom": False},
            ],
        )
        result = engine.evaluate(ctx)
        assert not result.overall_passed
        assert not result.checks[0].passed
        assert result.blocking_failures == 1

    def test_sbom_threshold_partial(self) -> None:
        """50% threshold should pass when 1/2 artifacts have SBOM."""
        engine = PolicyEngine(
            rules=[make_rule("R1", "artifact_has_sbom", threshold=0.5)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[
                {"artifact_id": "A1", "has_sbom": True},
                {"artifact_id": "A2", "has_sbom": False},
            ],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_no_artifacts_passes_sbom_check(self) -> None:
        """No artifacts → check should pass (nothing to check)."""
        engine = PolicyEngine(
            rules=[make_rule("R1", "artifact_has_sbom", threshold=1.0)]
        )
        ctx = ReleaseContext(release_id="REL-001", artifacts=[])
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_provenance_check_passes(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "artifact_has_provenance", threshold=1.0)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[{"artifact_id": "A1", "has_provenance": True}],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_provenance_check_fails(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "artifact_has_provenance", threshold=1.0)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[{"artifact_id": "A1", "has_provenance": False}],
        )
        result = engine.evaluate(ctx)
        assert not result.overall_passed


class TestPolicyEngineVulnChecks:
    def test_no_critical_vulns_passes(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "no_critical_vulns", max_allowed=0)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[{"artifact_id": "A1", "critical_vulns": 0, "high_vulns": 2}],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_critical_vulns_fails(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "no_critical_vulns", max_allowed=0)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[{"artifact_id": "A1", "critical_vulns": 2}],
        )
        result = engine.evaluate(ctx)
        assert not result.overall_passed

    def test_high_vulns_within_threshold(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "no_high_vulns_above_threshold", max_allowed=5)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[{"artifact_id": "A1", "high_vulns": 3}],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_high_vulns_exceeds_threshold(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "no_high_vulns_above_threshold", max_allowed=5)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[{"artifact_id": "A1", "high_vulns": 8}],
        )
        result = engine.evaluate(ctx)
        assert not result.overall_passed


class TestPolicyEngineControlsAndApprovals:
    def test_controls_all_implemented_passes(self) -> None:
        engine = PolicyEngine(
            rules=[
                make_rule(
                    "R1",
                    "controls_implemented",
                    required_controls=["AC-2", "AU-6"],
                )
            ]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            controls_implemented=["AC-2", "AU-6", "CM-3"],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_controls_missing_fails(self) -> None:
        engine = PolicyEngine(
            rules=[
                make_rule(
                    "R1",
                    "controls_implemented",
                    required_controls=["AC-2", "AU-6", "RA-5"],
                )
            ]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            controls_implemented=["AC-2"],
        )
        result = engine.evaluate(ctx)
        assert not result.overall_passed
        details = result.checks[0].details
        assert "AU-6" in details["missing"]
        assert "RA-5" in details["missing"]

    def test_approvals_all_present_passes(self) -> None:
        engine = PolicyEngine(
            rules=[
                make_rule(
                    "R1",
                    "required_approvals_present",
                    required_approvers=["ciso", "pm"],
                )
            ]
        )
        ctx = ReleaseContext(release_id="REL-001", approvers=["ciso", "pm", "eng"])
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_approvals_missing_fails(self) -> None:
        engine = PolicyEngine(
            rules=[
                make_rule(
                    "R1",
                    "required_approvals_present",
                    required_approvers=["ciso", "pm"],
                )
            ]
        )
        ctx = ReleaseContext(release_id="REL-001", approvers=["eng"])
        result = engine.evaluate(ctx)
        assert not result.overall_passed


class TestPolicyEngineExceptionsAndEvidence:
    def test_no_open_exceptions_passes(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "no_open_blocking_exceptions")]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            open_blocking_exceptions=[],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_open_exceptions_fails(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "no_open_blocking_exceptions")]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            open_blocking_exceptions=[{"exception_id": "EXC-001", "status": "open"}],
        )
        result = engine.evaluate(ctx)
        assert not result.overall_passed

    def test_evidence_freshness_passes(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "evidence_freshness_days", max_age_days=90)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            evidence_items=[
                {"evidence_id": "EV-001", "collected_at": datetime.now(UTC) - timedelta(days=10)},
            ],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_evidence_freshness_fails_for_stale(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "evidence_freshness_days", max_age_days=30)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            evidence_items=[
                {
                    "evidence_id": "EV-001",
                    "collected_at": datetime.now(UTC) - timedelta(days=95),
                }
            ],
        )
        result = engine.evaluate(ctx)
        assert not result.checks[0].passed

    def test_test_pass_rate_100_passes(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "test_pass_rate", min_pass_rate=1.0)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            test_results=[
                {"test_id": "TC-001", "result": "pass"},
                {"test_id": "TC-002", "result": "pass"},
            ],
        )
        result = engine.evaluate(ctx)
        assert result.overall_passed

    def test_test_pass_rate_fails(self) -> None:
        engine = PolicyEngine(
            rules=[make_rule("R1", "test_pass_rate", min_pass_rate=1.0)]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            test_results=[
                {"test_id": "TC-001", "result": "pass"},
                {"test_id": "TC-002", "result": "fail"},
            ],
        )
        result = engine.evaluate(ctx)
        assert not result.overall_passed

    def test_no_tests_registered_passes(self) -> None:
        """No test results → should pass (informational)."""
        engine = PolicyEngine(
            rules=[make_rule("R1", "test_pass_rate", min_pass_rate=1.0)]
        )
        ctx = ReleaseContext(release_id="REL-001", test_results=[])
        result = engine.evaluate(ctx)
        assert result.overall_passed


class TestPolicyEngineMultiRule:
    def test_compliance_score_calculation(self) -> None:
        engine = PolicyEngine(
            rules=[
                make_rule("R1", "artifact_has_sbom", threshold=1.0),
                make_rule("R2", "no_critical_vulns", max_allowed=0),
                make_rule("R3", "always_pass"),
            ]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[{"artifact_id": "A1", "has_sbom": True, "critical_vulns": 0}],
        )
        result = engine.evaluate(ctx)
        assert result.compliance_score == 100.0
        assert result.blocking_failures == 0
        assert result.overall_passed

    def test_partial_failures_score(self) -> None:
        engine = PolicyEngine(
            rules=[
                make_rule("R1", "artifact_has_sbom", threshold=1.0, blocking=True),
                make_rule("R2", "artifact_has_provenance", threshold=1.0, blocking=False),
                make_rule("R3", "always_pass"),
            ]
        )
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[
                {"artifact_id": "A1", "has_sbom": False, "has_provenance": False}
            ],
        )
        result = engine.evaluate(ctx)
        # 1 out of 3 pass → 33.3% score
        assert result.compliance_score == pytest.approx(33.3, abs=0.1)
        # Only R1 is blocking, so 1 blocking failure
        assert result.blocking_failures == 1
        assert not result.overall_passed

    def test_disabled_rules_skipped(self) -> None:
        rule = make_rule("R1", "no_critical_vulns", max_allowed=0)
        rule.enabled = False
        engine = PolicyEngine(rules=[rule])
        ctx = ReleaseContext(
            release_id="REL-001",
            artifacts=[{"artifact_id": "A1", "critical_vulns": 5}],
        )
        result = engine.evaluate(ctx)
        # Disabled rule is skipped → no checks → passes
        assert result.overall_passed
        assert result.total_checks == 0

    def test_unknown_condition_type_fails(self) -> None:
        rule = make_rule("R1", "nonexistent_condition_type")
        engine = PolicyEngine(rules=[rule])
        ctx = ReleaseContext(release_id="REL-001")
        result = engine.evaluate(ctx)
        assert not result.checks[0].passed

    def test_always_pass_condition(self) -> None:
        rule = make_rule("R1", "always_pass")
        engine = PolicyEngine(rules=[rule])
        ctx = ReleaseContext(release_id="REL-001")
        result = engine.evaluate(ctx)
        assert result.checks[0].passed


class TestPolicyEngineFromYAML:
    def test_load_from_yaml_string(self) -> None:
        yaml_content = """
rules:
  - id: RULE-001
    name: SBOM Required
    category: supply-chain
    severity: critical
    blocking: true
    condition:
      type: artifact_has_sbom
      threshold: 1.0
  - id: RULE-002
    name: No Critical Vulns
    category: vuln
    severity: critical
    blocking: true
    condition:
      type: no_critical_vulns
      max_allowed: 0
"""
        engine = PolicyEngine.from_yaml(yaml_content)
        assert len(engine.rules) == 2
        assert engine.rules[0].rule_id == "RULE-001"
        assert engine.rules[1].rule_id == "RULE-002"
        assert engine.rules[0].condition.condition_type == "artifact_has_sbom"
        assert engine.rules[0].condition.params["threshold"] == 1.0

    def test_default_engine_has_rules(self) -> None:
        engine = get_default_policy_engine()
        assert len(engine.rules) > 0
        rule_ids = [r.rule_id for r in engine.rules]
        assert "RULE-001" in rule_ids

    def test_default_engine_evaluates_compliant_release(self) -> None:
        engine = get_default_policy_engine()
        ctx = ReleaseContext(
            release_id="REL-TEST",
            artifacts=[
                {
                    "artifact_id": "A1",
                    "has_sbom": True,
                    "has_provenance": True,
                    "has_signature": True,
                    "critical_vulns": 0,
                    "high_vulns": 0,
                }
            ],
            controls_implemented=["AC-2", "AC-3", "AU-6", "CA-7", "CM-3", "RA-5", "SI-2"],
            approvers=[],
            open_blocking_exceptions=[],
            evidence_items=[
                {
                    "evidence_id": "EV-001",
                    "collected_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                }
            ],
            test_results=[{"result": "pass"}, {"result": "pass"}],
        )
        result = engine.evaluate(ctx)
        # Controls_implemented check uses ctx.required_controls which defaults to empty → passes
        blocking_fails = [c for c in result.checks if not c.passed and c.blocking]
        # The compliant release should have no blocking failures from SBOM/vulns/exceptions checks
        sbom_check = next(c for c in result.checks if c.rule_id == "RULE-001")
        vuln_check = next(c for c in result.checks if c.rule_id == "RULE-003")
        assert sbom_check.passed
        assert vuln_check.passed
