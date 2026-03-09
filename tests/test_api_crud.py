"""Comprehensive API integration tests for all CRUD endpoints."""

from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Requirements API
# ---------------------------------------------------------------------------


class TestRequirementsAPI:
    async def test_list_requirements_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/requirements")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_requirement(self, client: AsyncClient) -> None:
        payload = {
            "req_id": "REQ-001",
            "title": "Authentication must use MFA",
            "req_type": "security",
            "status": "draft",
        }
        resp = await client.post("/api/v1/requirements", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["req_id"] == "REQ-001"
        assert data["title"] == "Authentication must use MFA"
        assert data["is_completed"] is False

    async def test_create_requirement_conflict(self, client: AsyncClient) -> None:
        payload = {
            "req_id": "REQ-DUP",
            "title": "Duplicate",
            "req_type": "system",
            "status": "draft",
        }
        await client.post("/api/v1/requirements", json=payload)
        resp = await client.post("/api/v1/requirements", json=payload)
        assert resp.status_code == 409

    async def test_get_requirement(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/requirements",
            json={
                "req_id": "REQ-002",
                "title": "Audit logging",
                "req_type": "regulatory",
                "status": "approved",
            },
        )
        resp = await client.get("/api/v1/requirements/REQ-002")
        assert resp.status_code == 200
        assert resp.json()["req_id"] == "REQ-002"

    async def test_get_requirement_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/requirements/REQ-MISSING")
        assert resp.status_code == 404

    async def test_list_requirements_filter_status(self, client: AsyncClient) -> None:
        for i, st in enumerate(["draft", "approved", "verified"]):
            await client.post(
                "/api/v1/requirements",
                json={
                    "req_id": f"REQ-F{i}",
                    "title": f"Req {i}",
                    "req_type": "system",
                    "status": st,
                },
            )
        resp = await client.get("/api/v1/requirements?status=approved")
        assert resp.status_code == 200
        data = resp.json()
        assert all(r["status"] == "approved" for r in data)

    async def test_update_requirement(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/requirements",
            json={
                "req_id": "REQ-UPD",
                "title": "Original",
                "req_type": "system",
                "status": "draft",
            },
        )
        resp = await client.put(
            "/api/v1/requirements/REQ-UPD",
            json={
                "req_id": "REQ-UPD",
                "title": "Updated",
                "req_type": "system",
                "status": "approved",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"
        assert resp.json()["status"] == "approved"

    async def test_patch_requirement(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/requirements",
            json={
                "req_id": "REQ-PATCH",
                "title": "Patchable",
                "req_type": "system",
                "status": "draft",
            },
        )
        resp = await client.patch(
            "/api/v1/requirements/REQ-PATCH",
            json={
                "req_id": "REQ-PATCH",
                "title": "Patchable",
                "req_type": "system",
                "status": "implemented",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "implemented"

    async def test_delete_requirement(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/requirements",
            json={
                "req_id": "REQ-DEL",
                "title": "To delete",
                "req_type": "system",
                "status": "draft",
            },
        )
        resp = await client.delete("/api/v1/requirements/REQ-DEL")
        assert resp.status_code == 204
        resp2 = await client.get("/api/v1/requirements/REQ-DEL")
        assert resp2.status_code == 404

    async def test_count_requirements(self, client: AsyncClient) -> None:
        for i in range(3):
            await client.post(
                "/api/v1/requirements",
                json={
                    "req_id": f"REQ-CNT-{i}",
                    "title": f"Req {i}",
                    "req_type": "system",
                    "status": "draft",
                },
            )
        resp = await client.get("/api/v1/requirements/count")
        assert resp.status_code == 200
        assert resp.json()["count"] == 3

    async def test_verified_requirement_is_completed(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/requirements",
            json={
                "req_id": "REQ-DONE",
                "title": "Verified",
                "req_type": "system",
                "status": "verified",
            },
        )
        resp = await client.get("/api/v1/requirements/REQ-DONE")
        assert resp.status_code == 200
        assert resp.json()["is_completed"] is True


# ---------------------------------------------------------------------------
# Controls API
# ---------------------------------------------------------------------------


class TestControlsAPI:
    async def test_list_controls_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/controls")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_control(self, client: AsyncClient) -> None:
        payload = {
            "control_id": "AC-2",
            "family": "AC",
            "title": "Account Management",
            "framework": "NIST-800-53-Rev5",
        }
        resp = await client.post("/api/v1/controls", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["control_id"] == "AC-2"

    async def test_create_control_conflict(self, client: AsyncClient) -> None:
        payload = {
            "control_id": "AC-DUP",
            "family": "AC",
            "title": "Dup",
            "framework": "NIST-800-53-Rev5",
        }
        await client.post("/api/v1/controls", json=payload)
        resp = await client.post("/api/v1/controls", json=payload)
        assert resp.status_code == 409

    async def test_get_control(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/controls",
            json={
                "control_id": "AU-2",
                "family": "AU",
                "title": "Event Logging",
                "framework": "NIST-800-53-Rev5",
            },
        )
        resp = await client.get("/api/v1/controls/AU-2")
        assert resp.status_code == 200
        assert resp.json()["control_id"] == "AU-2"

    async def test_get_control_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/controls/XX-999")
        assert resp.status_code == 404

    async def test_update_control(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/controls",
            json={
                "control_id": "SC-8",
                "family": "SC",
                "title": "Transmission",
                "framework": "NIST-800-53-Rev5",
            },
        )
        resp = await client.put(
            "/api/v1/controls/SC-8",
            json={
                "control_id": "SC-8",
                "family": "SC",
                "title": "Transmission Confidentiality",
                "framework": "NIST-800-53-Rev5",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Transmission Confidentiality"

    async def test_patch_control(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/controls",
            json={
                "control_id": "IA-2",
                "family": "IA",
                "title": "IA-2 Original",
                "framework": "NIST-800-53-Rev5",
            },
        )
        resp = await client.patch(
            "/api/v1/controls/IA-2",
            json={
                "control_id": "IA-2",
                "family": "IA",
                "title": "IA-2 Patched",
                "framework": "NIST-800-53-Rev5",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "IA-2 Patched"

    async def test_delete_control(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/controls",
            json={
                "control_id": "CA-1",
                "family": "CA",
                "title": "Policy and Procedures",
                "framework": "NIST-800-53-Rev5",
            },
        )
        resp = await client.delete("/api/v1/controls/CA-1")
        assert resp.status_code == 204
        resp2 = await client.get("/api/v1/controls/CA-1")
        assert resp2.status_code == 404

    async def test_list_controls_filter_family(self, client: AsyncClient) -> None:
        for cid, fam in [("AC-3", "AC"), ("AC-4", "AC"), ("AU-3", "AU")]:
            await client.post(
                "/api/v1/controls",
                json={
                    "control_id": cid,
                    "family": fam,
                    "title": cid,
                    "framework": "NIST-800-53-Rev5",
                },
            )
        resp = await client.get("/api/v1/controls?family=AC")
        assert resp.status_code == 200
        data = resp.json()
        assert all(c["family"] == "AC" for c in data)
        assert len(data) == 2


# ---------------------------------------------------------------------------
# Evidence API
# ---------------------------------------------------------------------------


class TestEvidenceAPI:
    async def test_list_evidence_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/evidence")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_evidence(self, client: AsyncClient) -> None:
        payload = {
            "evidence_id": "EV-001",
            "title": "CI pipeline run",
            "evidence_type": "ci_run",
            "status": "valid",
        }
        resp = await client.post("/api/v1/evidence", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["evidence_id"] == "EV-001"
        assert data["status"] == "valid"

    async def test_create_evidence_conflict(self, client: AsyncClient) -> None:
        payload = {
            "evidence_id": "EV-DUP",
            "title": "Dup",
            "evidence_type": "ci_run",
            "status": "valid",
        }
        await client.post("/api/v1/evidence", json=payload)
        resp = await client.post("/api/v1/evidence", json=payload)
        assert resp.status_code == 409

    async def test_get_evidence(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/evidence",
            json={
                "evidence_id": "EV-002",
                "title": "SAST scan",
                "evidence_type": "static_analysis",
                "status": "valid",
            },
        )
        resp = await client.get("/api/v1/evidence/EV-002")
        assert resp.status_code == 200
        assert resp.json()["evidence_id"] == "EV-002"

    async def test_get_evidence_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/evidence/EV-MISSING")
        assert resp.status_code == 404

    async def test_update_evidence(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/evidence",
            json={
                "evidence_id": "EV-UPD",
                "title": "Old",
                "evidence_type": "ci_run",
                "status": "pending",
            },
        )
        resp = await client.put(
            "/api/v1/evidence/EV-UPD",
            json={
                "evidence_id": "EV-UPD",
                "title": "Updated",
                "evidence_type": "ci_run",
                "status": "valid",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "valid"

    async def test_patch_evidence(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/evidence",
            json={
                "evidence_id": "EV-PATCH",
                "title": "Patchable",
                "evidence_type": "ci_run",
                "status": "pending",
            },
        )
        resp = await client.patch(
            "/api/v1/evidence/EV-PATCH",
            json={
                "evidence_id": "EV-PATCH",
                "title": "Patchable",
                "evidence_type": "ci_run",
                "status": "valid",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "valid"

    async def test_delete_evidence(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/evidence",
            json={
                "evidence_id": "EV-DEL",
                "title": "To delete",
                "evidence_type": "ci_run",
                "status": "valid",
            },
        )
        resp = await client.delete("/api/v1/evidence/EV-DEL")
        assert resp.status_code == 204
        resp2 = await client.get("/api/v1/evidence/EV-DEL")
        assert resp2.status_code == 404


# ---------------------------------------------------------------------------
# Releases API
# ---------------------------------------------------------------------------


class TestReleasesAPI:
    async def test_list_releases_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/releases")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_release(self, client: AsyncClient) -> None:
        payload = {
            "release_id": "REL-1.0.0",
            "name": "Initial Release",
            "version": "1.0.0",
            "status": "draft",
        }
        resp = await client.post("/api/v1/releases", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["release_id"] == "REL-1.0.0"
        assert data["status"] == "draft"

    async def test_create_release_conflict(self, client: AsyncClient) -> None:
        payload = {"release_id": "REL-DUP", "name": "Dup", "version": "0.0.0", "status": "draft"}
        await client.post("/api/v1/releases", json=payload)
        resp = await client.post("/api/v1/releases", json=payload)
        assert resp.status_code == 409

    async def test_get_release(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/releases",
            json={
                "release_id": "REL-2.0.0",
                "name": "V2",
                "version": "2.0.0",
                "status": "candidate",
            },
        )
        resp = await client.get("/api/v1/releases/REL-2.0.0")
        assert resp.status_code == 200
        assert resp.json()["release_id"] == "REL-2.0.0"

    async def test_get_release_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/releases/REL-MISSING")
        assert resp.status_code == 404

    async def test_update_release(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/releases",
            json={"release_id": "REL-UPD", "name": "Old", "version": "1.0.0", "status": "draft"},
        )
        resp = await client.put(
            "/api/v1/releases/REL-UPD",
            json={
                "release_id": "REL-UPD",
                "name": "Updated",
                "version": "1.0.1",
                "status": "candidate",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "candidate"

    async def test_patch_release(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/releases",
            json={
                "release_id": "REL-PATCH",
                "name": "Patchable",
                "version": "1.0.0",
                "status": "draft",
            },
        )
        resp = await client.patch(
            "/api/v1/releases/REL-PATCH",
            json={
                "release_id": "REL-PATCH",
                "name": "Patchable",
                "version": "1.0.0",
                "status": "approved",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    async def test_delete_release(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/releases",
            json={
                "release_id": "REL-DEL",
                "name": "To delete",
                "version": "0.0.1",
                "status": "draft",
            },
        )
        resp = await client.delete("/api/v1/releases/REL-DEL")
        assert resp.status_code == 204
        resp2 = await client.get("/api/v1/releases/REL-DEL")
        assert resp2.status_code == 404

    async def test_list_releases_filter_status(self, client: AsyncClient) -> None:
        for i, st in enumerate(["draft", "approved", "blocked"]):
            await client.post(
                "/api/v1/releases",
                json={
                    "release_id": f"REL-F{i}",
                    "name": f"Release {i}",
                    "version": f"1.{i}.0",
                    "status": st,
                },
            )
        resp = await client.get("/api/v1/releases?status=approved")
        assert resp.status_code == 200
        data = resp.json()
        assert all(r["status"] == "approved" for r in data)


# ---------------------------------------------------------------------------
# Components API
# ---------------------------------------------------------------------------


class TestComponentsAPI:
    async def test_list_components_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/components")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_component(self, client: AsyncClient) -> None:
        payload = {
            "name": "auth-service",
            "component_type": "microservice",
            "description": "Authentication service",
            "version": "1.0.0",
        }
        resp = await client.post("/api/v1/components", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "auth-service"
        assert data["component_type"] == "microservice"

    async def test_create_component_conflict(self, client: AsyncClient) -> None:
        payload = {"name": "dup-svc", "component_type": "service"}
        await client.post("/api/v1/components", json=payload)
        resp = await client.post("/api/v1/components", json=payload)
        assert resp.status_code == 409

    async def test_get_component_by_id(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/components",
            json={"name": "get-test-svc", "component_type": "api"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/components/{comp_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "get-test-svc"

    async def test_get_component_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/components/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_list_components_filter_type(self, client: AsyncClient) -> None:
        for name, ctype in [
            ("svc-a", "microservice"),
            ("svc-b", "microservice"),
            ("db-c", "database"),
        ]:
            await client.post("/api/v1/components", json={"name": name, "component_type": ctype})
        resp = await client.get("/api/v1/components?component_type=microservice")
        assert resp.status_code == 200
        data = resp.json()
        assert all(c["component_type"] == "microservice" for c in data)
        assert len(data) == 2

    async def test_update_component(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/components",
            json={"name": "upd-svc", "component_type": "service"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.put(
            f"/api/v1/components/{comp_id}",
            json={"name": "upd-svc", "component_type": "microservice", "version": "2.0.0"},
        )
        assert resp.status_code == 200
        assert resp.json()["component_type"] == "microservice"

    async def test_patch_component(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/components",
            json={"name": "patch-svc", "component_type": "service"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/components/{comp_id}",
            json={"name": "patch-svc", "component_type": "service", "version": "3.0.0"},
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == "3.0.0"

    async def test_delete_component(self, client: AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/components",
            json={"name": "del-svc", "component_type": "service"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/components/{comp_id}")
        assert resp.status_code == 204
        resp2 = await client.get(f"/api/v1/components/{comp_id}")
        assert resp2.status_code == 404


# ---------------------------------------------------------------------------
# SBOM API
# ---------------------------------------------------------------------------


class TestSBOMAPI:
    async def test_list_sbom_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/sbom")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_sbom(self, client: AsyncClient) -> None:
        payload = {
            "sbom_id": "SBOM-001",
            "format": "cyclonedx",
            "spec_version": "1.4",
            "component_count": 42,
        }
        resp = await client.post("/api/v1/sbom", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["sbom_id"] == "SBOM-001"
        assert data["format"] == "cyclonedx"
        assert data["component_count"] == 42

    async def test_create_sbom_conflict(self, client: AsyncClient) -> None:
        payload = {"sbom_id": "SBOM-DUP", "format": "spdx"}
        await client.post("/api/v1/sbom", json=payload)
        resp = await client.post("/api/v1/sbom", json=payload)
        assert resp.status_code == 409

    async def test_get_sbom(self, client: AsyncClient) -> None:
        await client.post("/api/v1/sbom", json={"sbom_id": "SBOM-002", "format": "spdx"})
        resp = await client.get("/api/v1/sbom/SBOM-002")
        assert resp.status_code == 200
        assert resp.json()["sbom_id"] == "SBOM-002"

    async def test_get_sbom_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/sbom/SBOM-MISSING")
        assert resp.status_code == 404

    async def test_update_sbom(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/sbom", json={"sbom_id": "SBOM-UPD", "format": "spdx", "component_count": 5}
        )
        resp = await client.put(
            "/api/v1/sbom/SBOM-UPD",
            json={"sbom_id": "SBOM-UPD", "format": "cyclonedx", "component_count": 10},
        )
        assert resp.status_code == 200
        assert resp.json()["format"] == "cyclonedx"
        assert resp.json()["component_count"] == 10

    async def test_patch_sbom(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/sbom", json={"sbom_id": "SBOM-PATCH", "format": "spdx", "component_count": 0}
        )
        resp = await client.patch(
            "/api/v1/sbom/SBOM-PATCH",
            json={"sbom_id": "SBOM-PATCH", "format": "spdx", "component_count": 99},
        )
        assert resp.status_code == 200
        assert resp.json()["component_count"] == 99

    async def test_delete_sbom(self, client: AsyncClient) -> None:
        await client.post("/api/v1/sbom", json={"sbom_id": "SBOM-DEL", "format": "spdx"})
        resp = await client.delete("/api/v1/sbom/SBOM-DEL")
        assert resp.status_code == 204
        resp2 = await client.get("/api/v1/sbom/SBOM-DEL")
        assert resp2.status_code == 404

    async def test_list_sbom_filter_format(self, client: AsyncClient) -> None:
        for sid, fmt in [("SBOM-F1", "cyclonedx"), ("SBOM-F2", "cyclonedx"), ("SBOM-F3", "spdx")]:
            await client.post("/api/v1/sbom", json={"sbom_id": sid, "format": fmt})
        resp = await client.get("/api/v1/sbom?format=cyclonedx")
        assert resp.status_code == 200
        data = resp.json()
        assert all(s["format"] == "cyclonedx" for s in data)
        assert len(data) == 2


# ---------------------------------------------------------------------------
# Incidents API
# ---------------------------------------------------------------------------


class TestIncidentsAPI:
    async def test_list_incidents_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/incidents")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_incident(self, client: AsyncClient) -> None:
        payload = {
            "incident_id": "INC-001",
            "title": "Critical auth bypass",
            "severity": "critical",
            "status": "open",
        }
        resp = await client.post("/api/v1/incidents", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["incident_id"] == "INC-001"
        assert data["severity"] == "critical"

    async def test_create_incident_conflict(self, client: AsyncClient) -> None:
        payload = {"incident_id": "INC-DUP", "title": "Dup", "severity": "high", "status": "open"}
        await client.post("/api/v1/incidents", json=payload)
        resp = await client.post("/api/v1/incidents", json=payload)
        assert resp.status_code == 409

    async def test_get_incident(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/incidents",
            json={
                "incident_id": "INC-002",
                "title": "SQL injection",
                "severity": "high",
                "status": "open",
            },
        )
        resp = await client.get("/api/v1/incidents/INC-002")
        assert resp.status_code == 200
        assert resp.json()["incident_id"] == "INC-002"

    async def test_get_incident_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/incidents/INC-MISSING")
        assert resp.status_code == 404

    async def test_patch_incident(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/incidents",
            json={
                "incident_id": "INC-PATCH",
                "title": "Open",
                "severity": "medium",
                "status": "open",
            },
        )
        resp = await client.patch(
            "/api/v1/incidents/INC-PATCH",
            json={
                "incident_id": "INC-PATCH",
                "title": "Resolved",
                "severity": "medium",
                "status": "resolved",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

    async def test_delete_incident(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/incidents",
            json={
                "incident_id": "INC-DEL",
                "title": "To delete",
                "severity": "low",
                "status": "open",
            },
        )
        resp = await client.delete("/api/v1/incidents/INC-DEL")
        assert resp.status_code == 204

    async def test_list_exceptions_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/incidents/exceptions/list")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_exception(self, client: AsyncClient) -> None:
        payload = {
            "exception_id": "EXC-001",
            "title": "Accepted risk for legacy TLS",
            "status": "open",
            "approver": "CISO",
        }
        resp = await client.post("/api/v1/incidents/exceptions", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["exception_id"] == "EXC-001"

    async def test_get_exception(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/incidents/exceptions",
            json={"exception_id": "EXC-002", "title": "Exception 2", "status": "open"},
        )
        resp = await client.get("/api/v1/incidents/exceptions/EXC-002")
        assert resp.status_code == 200
        assert resp.json()["exception_id"] == "EXC-002"

    async def test_delete_exception(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/incidents/exceptions",
            json={"exception_id": "EXC-DEL", "title": "To delete", "status": "open"},
        )
        resp = await client.delete("/api/v1/incidents/exceptions/EXC-DEL")
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Metrics API
# ---------------------------------------------------------------------------


class TestMetricsAPI:
    async def test_metrics_empty_db(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "requirements" in data
        assert "controls" in data
        assert "evidence" in data
        assert "releases" in data
        assert "incidents" in data
        assert "exceptions" in data
        assert "supply_chain" in data
        assert "governance" in data
        assert data["requirements"]["total"] == 0
        assert data["evidence"]["validity_pct"] == 0.0

    async def test_metrics_with_data(self, client: AsyncClient) -> None:
        # Add some data
        await client.post(
            "/api/v1/requirements",
            json={
                "req_id": "REQ-M1",
                "title": "Metric Req 1",
                "req_type": "system",
                "status": "verified",
            },
        )
        await client.post(
            "/api/v1/evidence",
            json={
                "evidence_id": "EV-M1",
                "title": "Metric EV 1",
                "evidence_type": "ci_run",
                "status": "valid",
            },
        )
        await client.post("/api/v1/sbom", json={"sbom_id": "SBOM-M1", "format": "cyclonedx"})

        resp = await client.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["requirements"]["total"] == 1
        assert data["requirements"]["verified"] == 1
        assert data["requirements"]["completion_pct"] == 100.0
        assert data["evidence"]["total"] == 1
        assert data["evidence"]["valid"] == 1
        assert data["evidence"]["validity_pct"] == 100.0
        assert data["supply_chain"]["sbom_records"] == 1


# ---------------------------------------------------------------------------
# Traceability API
# ---------------------------------------------------------------------------


class TestTraceabilityAPI:
    async def test_get_full_graph_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/traceability/graph")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert data["nodes"] == []
        assert data["edges"] == []

    async def test_get_traceability_stats_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/traceability/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requirements" in data
        assert "total_controls" in data
        assert data["total_requirements"] == 0

    async def test_get_traceability_gaps_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/traceability/gaps")
        assert resp.status_code == 200
        data = resp.json()
        assert "untested_requirements" in data
        assert "unmapped_requirements" in data
        assert "controls_without_evidence" in data
        assert "stats" in data

    async def test_get_requirement_trace_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/traceability/graph/requirement/REQ-NOT-THERE")
        assert resp.status_code == 404

    async def test_get_control_trace_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/traceability/graph/control/AC-NOT-THERE")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Policy API
# ---------------------------------------------------------------------------


class TestPoliciesAPI:
    async def test_list_default_rules(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/policies/rules")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        rule = data[0]
        assert "rule_id" in rule
        assert "name" in rule
        assert "severity" in rule
        assert "blocking" in rule

    async def test_evaluate_policy_not_found(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/policies/evaluate/REL-MISSING")
        assert resp.status_code == 404

    async def test_evaluate_policy_for_release(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/releases",
            json={
                "release_id": "REL-POL-1",
                "name": "Policy Test",
                "version": "1.0.0",
                "status": "candidate",
            },
        )
        resp = await client.post("/api/v1/policies/evaluate/REL-POL-1")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_passed" in data
        assert "compliance_score" in data
        assert "checks" in data
        assert isinstance(data["checks"], list)


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------


class TestHealthEndpoints:
    async def test_health_check(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.2.0"

    async def test_root(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "version" in data
        assert data["version"] == "0.2.0"
