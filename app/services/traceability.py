"""Traceability engine using NetworkX directed graphs.

Builds a directed graph of entities and their relationships:
  Requirement → Control → Evidence
  Requirement → TestCase
  Requirement → Release
  Release → Artifact → SBOMRecord

Exposes methods to:
- add nodes / edges
- query forward/backward traces
- detect gaps (untested requirements, controls without evidence)
- export graph as JSON for visualization
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from app.schemas import TraceabilityEdge, TraceabilityGraph, TraceabilityNode


@dataclass
class TraceabilityEngine:
    """In-memory directed graph for traceability analysis."""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        status: str | None = None,
        **metadata: Any,
    ) -> None:
        self.graph.add_node(
            node_id,
            node_type=node_type,
            label=label,
            status=status,
            metadata=metadata,
        )

    def add_edge(self, source: str, target: str, relationship: str) -> None:
        self.graph.add_edge(source, target, relationship=relationship)

    # ------------------------------------------------------------------
    # Convenience builders
    # ------------------------------------------------------------------

    def add_requirement(
        self,
        req_id: str,
        title: str,
        status: str = "draft",
        **kw: Any,
    ) -> None:
        self.add_node(req_id, "requirement", title, status=status, **kw)

    def add_control(
        self,
        control_id: str,
        title: str,
        status: str = "not_implemented",
        **kw: Any,
    ) -> None:
        self.add_node(control_id, "control", title, status=status, **kw)

    def add_evidence(
        self,
        evidence_id: str,
        title: str,
        evidence_type: str = "ci_run",
        status: str = "valid",
        **kw: Any,
    ) -> None:
        self.add_node(
            evidence_id, "evidence", title, status=status, evidence_type=evidence_type, **kw
        )

    def add_test_case(self, test_id: str, name: str, result: str | None = None, **kw: Any) -> None:
        self.add_node(test_id, "test_case", name, status=result, **kw)

    def add_release(self, release_id: str, name: str, status: str = "draft", **kw: Any) -> None:
        self.add_node(release_id, "release", name, status=status, **kw)

    def add_artifact(self, artifact_id: str, name: str, **kw: Any) -> None:
        self.add_node(artifact_id, "artifact", name, **kw)

    def link_requirement_to_control(self, req_id: str, control_id: str) -> None:
        self.add_edge(req_id, control_id, "satisfies")

    def link_requirement_to_test(self, req_id: str, test_id: str) -> None:
        self.add_edge(req_id, test_id, "tested_by")

    def link_control_to_evidence(self, control_id: str, evidence_id: str) -> None:
        self.add_edge(control_id, evidence_id, "evidenced_by")

    def link_release_to_requirement(self, release_id: str, req_id: str) -> None:
        self.add_edge(release_id, req_id, "includes")

    def link_release_to_artifact(self, release_id: str, artifact_id: str) -> None:
        self.add_edge(release_id, artifact_id, "contains")

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        if node_id not in self.graph:
            return None
        attrs = self.graph.nodes[node_id]
        return {"node_id": node_id, **attrs}

    def get_downstream(self, node_id: str) -> list[dict[str, Any]]:
        """Return all nodes reachable from node_id (forward trace)."""
        descendants = nx.descendants(self.graph, node_id)
        return [self.get_node_by_id(n) for n in descendants if n is not None]

    def get_upstream(self, node_id: str) -> list[dict[str, Any]]:
        """Return all nodes from which node_id is reachable (backward trace)."""
        ancestors = nx.ancestors(self.graph, node_id)
        return [self.get_node_by_id(n) for n in ancestors if n is not None]

    def requirements_without_tests(self) -> list[str]:
        """Return req_ids of requirements that have no test_case successors."""
        result = []
        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") != "requirement":
                continue
            successors = list(self.graph.successors(node))
            has_test = any(self.graph.nodes[s].get("node_type") == "test_case" for s in successors)
            if not has_test:
                result.append(node)
        return result

    def requirements_without_controls(self) -> list[str]:
        """Return req_ids of requirements with no control mappings."""
        result = []
        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") != "requirement":
                continue
            successors = list(self.graph.successors(node))
            has_control = any(self.graph.nodes[s].get("node_type") == "control" for s in successors)
            if not has_control:
                result.append(node)
        return result

    def controls_without_evidence(self) -> list[str]:
        """Return control_ids with no evidence items."""
        result = []
        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") != "control":
                continue
            successors = list(self.graph.successors(node))
            has_evidence = any(
                self.graph.nodes[s].get("node_type") == "evidence" for s in successors
            )
            if not has_evidence:
                result.append(node)
        return result

    def coverage_stats(self) -> dict[str, Any]:
        """Return coverage statistics across the traceability graph."""
        all_reqs = [
            n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "requirement"
        ]
        all_controls = [
            n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "control"
        ]

        untested = self.requirements_without_tests()
        unmapped = self.requirements_without_controls()
        no_evidence = self.controls_without_evidence()

        return {
            "total_requirements": len(all_reqs),
            "untested_requirements": len(untested),
            "unmapped_requirements": len(unmapped),
            "total_controls": len(all_controls),
            "controls_without_evidence": len(no_evidence),
            "req_test_coverage_pct": round(
                (1 - len(untested) / len(all_reqs)) * 100 if all_reqs else 0, 1
            ),
            "req_control_coverage_pct": round(
                (1 - len(unmapped) / len(all_reqs)) * 100 if all_reqs else 0, 1
            ),
            "control_evidence_coverage_pct": round(
                (1 - len(no_evidence) / len(all_controls)) * 100 if all_controls else 0, 1
            ),
        }

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_schema(
        self,
        root_id: str | None = None,
        node_type_filter: str | None = None,
    ) -> TraceabilityGraph:
        """Export the graph (or subgraph) as a TraceabilityGraph schema."""
        if root_id:
            sub_nodes: set[str] = {root_id}
            sub_nodes |= nx.descendants(self.graph, root_id)
            sub_nodes |= nx.ancestors(self.graph, root_id)
            subgraph = self.graph.subgraph(sub_nodes)
        else:
            subgraph = self.graph

        nodes = []
        for node_id, attrs in subgraph.nodes(data=True):
            if node_type_filter and attrs.get("node_type") != node_type_filter:
                continue
            nodes.append(
                TraceabilityNode(
                    node_id=node_id,
                    node_type=attrs.get("node_type", "unknown"),
                    label=attrs.get("label", node_id),
                    status=attrs.get("status"),
                    metadata=attrs.get("metadata"),
                )
            )

        edges = []
        for src, tgt, edata in subgraph.edges(data=True):
            if node_type_filter and (
                subgraph.nodes[src].get("node_type") != node_type_filter
                and subgraph.nodes[tgt].get("node_type") != node_type_filter
            ):
                continue
            edges.append(
                TraceabilityEdge(
                    source=src,
                    target=tgt,
                    relationship=edata.get("relationship", "related_to"),
                )
            )

        return TraceabilityGraph(nodes=nodes, edges=edges)

    def to_dict(self) -> dict[str, Any]:
        """Export graph as plain dict for JSON serialization."""
        return {
            "nodes": [{"id": n, **d} for n, d in self.graph.nodes(data=True)],
            "edges": [{"source": u, "target": v, **d} for u, v, d in self.graph.edges(data=True)],
            "stats": self.coverage_stats(),
        }


def build_engine_from_db_data(
    requirements: list[Any],
    controls: list[Any],
    evidence_items: list[Any],
    test_cases: list[Any],
    releases: list[Any],
) -> TraceabilityEngine:
    """Construct a TraceabilityEngine from ORM model instances."""
    engine = TraceabilityEngine()

    for req in requirements:
        engine.add_requirement(
            req.req_id,
            req.title,
            status=req.status.value if hasattr(req.status, "value") else str(req.status),
        )
        for ctrl in getattr(req, "controls", []):
            if not engine.graph.has_node(ctrl.control_id):
                engine.add_control(ctrl.control_id, ctrl.title)
            engine.link_requirement_to_control(req.req_id, ctrl.control_id)
        for tc in getattr(req, "test_cases", []):
            engine.add_test_case(tc.test_id, tc.name, result=tc.last_result)
            engine.link_requirement_to_test(req.req_id, tc.test_id)

    for ctrl in controls:
        if not engine.graph.has_node(ctrl.control_id):
            engine.add_control(ctrl.control_id, ctrl.title)
        for ev in getattr(ctrl, "evidence_items", []):
            engine.add_evidence(ev.evidence_id, ev.title, status=ev.status.value)
            engine.link_control_to_evidence(ctrl.control_id, ev.evidence_id)

    for rel in releases:
        engine.add_release(
            rel.release_id,
            rel.name,
            status=rel.status.value if hasattr(rel.status, "value") else str(rel.status),
        )
        for req in getattr(rel, "requirements", []):
            engine.link_release_to_requirement(rel.release_id, req.req_id)
        for art in getattr(rel, "artifacts", []):
            engine.add_artifact(art.artifact_id, art.name)
            engine.link_release_to_artifact(rel.release_id, art.artifact_id)

    return engine
