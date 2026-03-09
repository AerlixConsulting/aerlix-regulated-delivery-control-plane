"""Tests for the TraceabilityEngine."""


from app.services.traceability import TraceabilityEngine, build_engine_from_db_data


class TestTraceabilityEngine:
    def setup_method(self) -> None:
        self.engine = TraceabilityEngine()

    def test_add_and_retrieve_node(self) -> None:
        self.engine.add_requirement("REQ-001", "Auth required", status="approved")
        node = self.engine.get_node_by_id("REQ-001")
        assert node is not None
        assert node["node_type"] == "requirement"
        assert node["label"] == "Auth required"
        assert node["status"] == "approved"

    def test_add_edge(self) -> None:
        self.engine.add_requirement("REQ-001", "Auth required")
        self.engine.add_control("AC-2", "Account Management")
        self.engine.link_requirement_to_control("REQ-001", "AC-2")
        assert self.engine.graph.has_edge("REQ-001", "AC-2")

    def test_get_downstream(self) -> None:
        self.engine.add_requirement("REQ-001", "Auth required")
        self.engine.add_control("AC-2", "Account Management")
        self.engine.add_evidence("EV-001", "CI Run", status="valid")
        self.engine.link_requirement_to_control("REQ-001", "AC-2")
        self.engine.link_control_to_evidence("AC-2", "EV-001")

        downstream = self.engine.get_downstream("REQ-001")
        node_ids = {n["node_id"] for n in downstream}
        assert "AC-2" in node_ids
        assert "EV-001" in node_ids

    def test_get_upstream(self) -> None:
        self.engine.add_requirement("REQ-001", "Auth required")
        self.engine.add_control("AC-2", "Account Management")
        self.engine.link_requirement_to_control("REQ-001", "AC-2")

        upstream = self.engine.get_upstream("AC-2")
        node_ids = {n["node_id"] for n in upstream}
        assert "REQ-001" in node_ids

    def test_requirements_without_tests(self) -> None:
        self.engine.add_requirement("REQ-001", "Auth required")
        self.engine.add_requirement("REQ-002", "Audit logs")
        self.engine.add_test_case("TC-001", "test_auth", result="pass")
        self.engine.link_requirement_to_test("REQ-001", "TC-001")

        untested = self.engine.requirements_without_tests()
        assert "REQ-002" in untested
        assert "REQ-001" not in untested

    def test_requirements_without_controls(self) -> None:
        self.engine.add_requirement("REQ-001", "Mapped")
        self.engine.add_requirement("REQ-002", "Unmapped")
        self.engine.add_control("AC-2", "Account Management")
        self.engine.link_requirement_to_control("REQ-001", "AC-2")

        unmapped = self.engine.requirements_without_controls()
        assert "REQ-002" in unmapped
        assert "REQ-001" not in unmapped

    def test_controls_without_evidence(self) -> None:
        self.engine.add_control("AC-2", "With evidence")
        self.engine.add_control("CM-3", "No evidence")
        self.engine.add_evidence("EV-001", "CI Run", status="valid")
        self.engine.link_control_to_evidence("AC-2", "EV-001")

        no_evidence = self.engine.controls_without_evidence()
        assert "CM-3" in no_evidence
        assert "AC-2" not in no_evidence

    def test_coverage_stats(self) -> None:
        self.engine.add_requirement("REQ-001", "With test and control")
        self.engine.add_requirement("REQ-002", "No test, no control")
        self.engine.add_control("AC-2", "With evidence")
        self.engine.add_control("CM-3", "No evidence")
        self.engine.add_test_case("TC-001", "Test")
        self.engine.add_evidence("EV-001", "Evidence")

        self.engine.link_requirement_to_control("REQ-001", "AC-2")
        self.engine.link_requirement_to_test("REQ-001", "TC-001")
        self.engine.link_control_to_evidence("AC-2", "EV-001")

        stats = self.engine.coverage_stats()
        assert stats["total_requirements"] == 2
        assert stats["total_controls"] == 2
        assert stats["untested_requirements"] == 1
        assert stats["unmapped_requirements"] == 1
        assert stats["controls_without_evidence"] == 1
        assert stats["req_test_coverage_pct"] == 50.0
        assert stats["req_control_coverage_pct"] == 50.0
        assert stats["control_evidence_coverage_pct"] == 50.0

    def test_to_schema_full_graph(self) -> None:
        self.engine.add_requirement("REQ-001", "Auth required")
        self.engine.add_control("AC-2", "Account Management")
        self.engine.link_requirement_to_control("REQ-001", "AC-2")

        graph = self.engine.to_schema()
        node_ids = {n.node_id for n in graph.nodes}
        assert "REQ-001" in node_ids
        assert "AC-2" in node_ids
        assert len(graph.edges) == 1
        assert graph.edges[0].relationship == "satisfies"

    def test_to_schema_subgraph(self) -> None:
        self.engine.add_requirement("REQ-001", "Req1")
        self.engine.add_requirement("REQ-002", "Req2 — unrelated")
        self.engine.add_control("AC-2", "Control")
        self.engine.link_requirement_to_control("REQ-001", "AC-2")

        graph = self.engine.to_schema(root_id="REQ-001")
        node_ids = {n.node_id for n in graph.nodes}
        assert "REQ-001" in node_ids
        assert "AC-2" in node_ids
        assert "REQ-002" not in node_ids

    def test_to_dict(self) -> None:
        self.engine.add_requirement("REQ-001", "Auth required")
        self.engine.add_control("AC-2", "Account Management")
        self.engine.link_requirement_to_control("REQ-001", "AC-2")

        d = self.engine.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert "stats" in d
        assert len(d["nodes"]) == 2
        assert len(d["edges"]) == 1

    def test_empty_graph_stats(self) -> None:
        stats = self.engine.coverage_stats()
        assert stats["total_requirements"] == 0
        assert stats["total_controls"] == 0
        assert stats["req_test_coverage_pct"] == 0

    def test_release_linkage(self) -> None:
        self.engine.add_requirement("REQ-001", "Auth")
        self.engine.add_release("REL-001", "v1.0", status="approved")
        self.engine.add_artifact("ART-001", "payments-api:1.0")
        self.engine.link_release_to_requirement("REL-001", "REQ-001")
        self.engine.link_release_to_artifact("REL-001", "ART-001")

        graph = self.engine.to_schema(root_id="REL-001")
        node_ids = {n.node_id for n in graph.nodes}
        assert "REQ-001" in node_ids
        assert "ART-001" in node_ids


class TestBuildEngineFromDbData:
    """Test the ORM-to-engine builder with mock objects."""

    def test_build_from_empty_data(self) -> None:
        engine = build_engine_from_db_data(
            requirements=[],
            controls=[],
            evidence_items=[],
            test_cases=[],
            releases=[],
        )
        assert len(engine.graph.nodes) == 0

    def test_build_from_mock_data(self) -> None:
        class MockControl:
            control_id = "AC-2"
            title = "Account Management"
            status = "implemented"
            evidence_items = []

        class MockReq:
            req_id = "REQ-001"
            title = "Auth Required"
            status = type("S", (), {"value": "approved"})()
            controls = [MockControl()]
            test_cases = []

        engine = build_engine_from_db_data(
            requirements=[MockReq()],
            controls=[MockControl()],
            evidence_items=[],
            test_cases=[],
            releases=[],
        )
        assert "REQ-001" in engine.graph
        assert "AC-2" in engine.graph
        assert engine.graph.has_edge("REQ-001", "AC-2")
