"""Audit bundle exporter.

Generates structured JSON and Markdown audit packages containing:
  - Control summary
  - Evidence index
  - Traceability matrix
  - Release readiness report
  - Unresolved gaps
  - Exception register
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditExporter:
    """Builds audit bundles from aggregated control-plane data."""

    def __init__(
        self,
        release_id: str | None = None,
        framework: str = "NIST-800-53-Rev5",
        generated_by: str = "aerlix-control-plane",
    ) -> None:
        self.release_id = release_id
        self.framework = framework
        self.generated_by = generated_by
        self.generated_at = datetime.now(UTC).isoformat()
        self._data: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Data ingestion helpers
    # ------------------------------------------------------------------

    def add_controls(self, controls: list[dict[str, Any]]) -> None:
        self._data["controls"] = controls

    def add_requirements(self, requirements: list[dict[str, Any]]) -> None:
        self._data["requirements"] = requirements

    def add_evidence_items(self, evidence: list[dict[str, Any]]) -> None:
        self._data["evidence_items"] = evidence

    def add_release(self, release: dict[str, Any]) -> None:
        self._data["release"] = release

    def add_policy_evaluation(self, evaluation: dict[str, Any]) -> None:
        self._data["policy_evaluation"] = evaluation

    def add_exceptions(self, exceptions: list[dict[str, Any]]) -> None:
        self._data["exceptions"] = exceptions

    def add_incidents(self, incidents: list[dict[str, Any]]) -> None:
        self._data["incidents"] = incidents

    def add_artifacts(self, artifacts: list[dict[str, Any]]) -> None:
        self._data["artifacts"] = artifacts

    def add_traceability_stats(self, stats: dict[str, Any]) -> None:
        self._data["traceability_stats"] = stats

    # ------------------------------------------------------------------
    # Bundle construction
    # ------------------------------------------------------------------

    def build_bundle(self) -> dict[str, Any]:
        controls = self._data.get("controls", [])
        requirements = self._data.get("requirements", [])
        evidence = self._data.get("evidence_items", [])
        exceptions = self._data.get("exceptions", [])
        incidents = self._data.get("incidents", [])
        artifacts = self._data.get("artifacts", [])
        release = self._data.get("release")
        policy_eval = self._data.get("policy_evaluation")
        trace_stats = self._data.get("traceability_stats", {})

        # --- Control summary ---
        control_summary = self._build_control_summary(controls)

        # --- Evidence index ---
        evidence_index = self._build_evidence_index(evidence)

        # --- Traceability matrix ---
        traceability_matrix = self._build_traceability_matrix(requirements, controls, evidence)

        # --- Gaps ---
        gaps = self._identify_gaps(requirements, controls, evidence, artifacts)

        # --- Exception register ---
        exception_register = self._build_exception_register(exceptions)

        # --- Release readiness ---
        release_readiness = self._build_release_readiness(release, policy_eval, artifacts)

        bundle: dict[str, Any] = {
            "bundle_metadata": {
                "bundle_id": self._generate_bundle_id(),
                "title": f"Audit Bundle — {self.framework}",
                "release_id": self.release_id,
                "framework": self.framework,
                "generated_by": self.generated_by,
                "generated_at": self.generated_at,
                "schema_version": "1.0",
            },
            "control_summary": control_summary,
            "evidence_index": evidence_index,
            "traceability_matrix": traceability_matrix,
            "release_readiness": release_readiness,
            "gaps": gaps,
            "exception_register": exception_register,
            "incident_summary": self._build_incident_summary(incidents),
            "traceability_stats": trace_stats,
        }

        return bundle

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_control_summary(self, controls: list[dict]) -> dict[str, Any]:
        status_counts: dict[str, int] = {}
        for ctrl in controls:
            s = ctrl.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "total_controls": len(controls),
            "status_breakdown": status_counts,
            "implemented_count": status_counts.get("implemented", 0)
            + status_counts.get("inherited", 0),
            "not_implemented_count": status_counts.get("not_implemented", 0),
            "controls": [
                {
                    "control_id": c.get("control_id"),
                    "title": c.get("title"),
                    "family": c.get("family"),
                    "status": c.get("status"),
                    "baseline": c.get("baseline"),
                }
                for c in controls
            ],
        }

    def _build_evidence_index(self, evidence: list[dict]) -> dict[str, Any]:
        type_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for ev in evidence:
            t = ev.get("evidence_type", "unknown")
            s = ev.get("status", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "total_evidence_items": len(evidence),
            "by_type": type_counts,
            "by_status": status_counts,
            "evidence_items": [
                {
                    "evidence_id": e.get("evidence_id"),
                    "title": e.get("title"),
                    "type": e.get("evidence_type"),
                    "status": e.get("status"),
                    "source_system": e.get("source_system"),
                    "collected_at": e.get("collected_at"),
                }
                for e in evidence
            ],
        }

    def _build_traceability_matrix(
        self,
        requirements: list[dict],
        controls: list[dict],
        evidence: list[dict],
    ) -> list[dict[str, Any]]:
        rows = []
        for req in requirements:
            linked_controls = [
                c.get("control_id") for c in req.get("controls", [])
            ]
            linked_tests = [t.get("test_id") for t in req.get("test_cases", [])]
            rows.append(
                {
                    "req_id": req.get("req_id"),
                    "title": req.get("title"),
                    "status": req.get("status"),
                    "linked_controls": linked_controls,
                    "linked_tests": linked_tests,
                    "has_controls": bool(linked_controls),
                    "has_tests": bool(linked_tests),
                }
            )
        return rows

    def _identify_gaps(
        self,
        requirements: list[dict],
        controls: list[dict],
        evidence: list[dict],
        artifacts: list[dict],
    ) -> dict[str, Any]:
        untested_reqs = [
            r.get("req_id")
            for r in requirements
            if not r.get("test_cases")
        ]
        unmapped_reqs = [
            r.get("req_id")
            for r in requirements
            if not r.get("controls")
        ]
        no_evidence_controls = [
            c.get("control_id")
            for c in controls
            if not c.get("evidence_items")
        ]
        artifacts_no_sbom = [
            a.get("artifact_id")
            for a in artifacts
            if not a.get("has_sbom")
        ]
        artifacts_no_provenance = [
            a.get("artifact_id")
            for a in artifacts
            if not a.get("has_provenance")
        ]

        return {
            "untested_requirements": untested_reqs,
            "unmapped_requirements": unmapped_reqs,
            "controls_without_evidence": no_evidence_controls,
            "artifacts_missing_sbom": artifacts_no_sbom,
            "artifacts_missing_provenance": artifacts_no_provenance,
            "total_gaps": (
                len(untested_reqs)
                + len(unmapped_reqs)
                + len(no_evidence_controls)
                + len(artifacts_no_sbom)
                + len(artifacts_no_provenance)
            ),
        }

    def _build_exception_register(self, exceptions: list[dict]) -> dict[str, Any]:
        open_exc = [e for e in exceptions if e.get("status") == "open"]
        return {
            "total_exceptions": len(exceptions),
            "open_exceptions": len(open_exc),
            "exceptions": [
                {
                    "exception_id": e.get("exception_id"),
                    "title": e.get("title"),
                    "status": e.get("status"),
                    "approver": e.get("approver"),
                    "expires_at": e.get("expires_at"),
                    "justification": e.get("justification"),
                }
                for e in exceptions
            ],
        }

    def _build_release_readiness(
        self,
        release: dict | None,
        policy_eval: dict | None,
        artifacts: list[dict],
    ) -> dict[str, Any]:
        if not release:
            return {"status": "no_release"}

        return {
            "release_id": release.get("release_id"),
            "version": release.get("version"),
            "status": release.get("status"),
            "policy_evaluation": policy_eval,
            "artifact_count": len(artifacts),
            "artifacts_with_sbom": sum(1 for a in artifacts if a.get("has_sbom")),
            "artifacts_with_provenance": sum(1 for a in artifacts if a.get("has_provenance")),
            "critical_vulns_total": sum(a.get("critical_vulns", 0) for a in artifacts),
            "high_vulns_total": sum(a.get("high_vulns", 0) for a in artifacts),
        }

    def _build_incident_summary(self, incidents: list[dict]) -> dict[str, Any]:
        open_inc = [i for i in incidents if i.get("status") not in ("resolved", "closed")]
        return {
            "total_incidents": len(incidents),
            "open_incidents": len(open_inc),
            "incidents": [
                {
                    "incident_id": i.get("incident_id"),
                    "title": i.get("title"),
                    "severity": i.get("severity"),
                    "status": i.get("status"),
                }
                for i in incidents
            ],
        }

    def _generate_bundle_id(self) -> str:
        raw = f"{self.release_id}:{self.generated_at}"
        return "BUNDLE-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_json(self, indent: int = 2) -> str:
        bundle = self.build_bundle()
        return json.dumps(bundle, indent=indent, default=str)

    def to_markdown(self) -> str:
        bundle = self.build_bundle()
        meta = bundle["bundle_metadata"]
        ctrl_summary = bundle["control_summary"]
        ev_index = bundle["evidence_index"]
        gaps = bundle["gaps"]
        rel_ready = bundle.get("release_readiness", {})
        exc_reg = bundle["exception_register"]

        lines = [
            f"# Audit Bundle: {meta['title']}",
            "",
            f"**Bundle ID:** `{meta['bundle_id']}`  ",
            f"**Framework:** {meta['framework']}  ",
            f"**Generated:** {meta['generated_at']}  ",
            f"**Generated By:** {meta['generated_by']}  ",
            "",
            "---",
            "",
            "## Control Summary",
            "",
            "| Metric | Count |",
            "|--------|-------|",
            f"| Total Controls | {ctrl_summary['total_controls']} |",
            f"| Implemented / Inherited | {ctrl_summary['implemented_count']} |",
            f"| Not Implemented | {ctrl_summary['not_implemented_count']} |",
            "",
            "---",
            "",
            "## Evidence Index",
            "",
            "| Metric | Count |",
            "|--------|-------|",
            f"| Total Evidence Items | {ev_index['total_evidence_items']} |",
        ]

        for ev_type, count in ev_index.get("by_type", {}).items():
            lines.append(f"| {ev_type} | {count} |")

        lines += [
            "",
            "---",
            "",
            "## Release Readiness",
            "",
        ]

        if rel_ready.get("release_id"):
            lines += [
                f"**Release:** `{rel_ready['release_id']}` — `{rel_ready['version']}`  ",
                f"**Status:** {rel_ready['status']}  ",
                f"**Critical Vulns:** {rel_ready.get('critical_vulns_total', 0)}  ",
                f"**High Vulns:** {rel_ready.get('high_vulns_total', 0)}  ",
            ]
        else:
            lines.append("_No release specified._")

        lines += [
            "",
            "---",
            "",
            "## Identified Gaps",
            "",
            f"- **Untested Requirements:** {len(gaps.get('untested_requirements', []))}",
            f"- **Unmapped Requirements:** {len(gaps.get('unmapped_requirements', []))}",
            f"- **Controls Without Evidence:** {len(gaps.get('controls_without_evidence', []))}",
            f"- **Artifacts Missing SBOM:** {len(gaps.get('artifacts_missing_sbom', []))}",
            f"- **Artifacts Missing Provenance:** {len(gaps.get('artifacts_missing_provenance', []))}",
            "",
            "---",
            "",
            "## Exception Register",
            "",
            f"**Total Exceptions:** {exc_reg['total_exceptions']}  ",
            f"**Open Exceptions:** {exc_reg['open_exceptions']}  ",
        ]

        if exc_reg["exceptions"]:
            lines += [
                "",
                "| ID | Title | Status | Approver | Expires |",
                "|----|-------|--------|----------|---------|",
            ]
            for exc in exc_reg["exceptions"]:
                lines.append(
                    f"| {exc.get('exception_id','')} | {exc.get('title','')} | "
                    f"{exc.get('status','')} | {exc.get('approver','')} | "
                    f"{exc.get('expires_at','')} |"
                )

        return "\n".join(lines)

    def save_json(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json())
        logger.info("Audit bundle written to %s", path)

    def save_markdown(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_markdown())
        logger.info("Audit bundle (Markdown) written to %s", path)
