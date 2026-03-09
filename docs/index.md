# Aerlix Regulated Delivery Control Plane

<div align="center">
  <strong>Compliance-native software delivery control plane for regulated environments.</strong>
</div>

---

## What It Is

The **Aerlix Regulated Delivery Control Plane** is a reference implementation platform that connects every artifact in regulated software delivery — from business requirements to deployed containers — through a unified, traceable, audit-ready system.

It is designed for engineering teams and compliance officers operating in:

- **FedRAMP**-aligned environments
- **NIST 800-53** controlled systems
- **PCI-DSS**, **HIPAA**, or **SOC 2** regulated pipelines
- **Continuous Authorization to Operate (cATO)** programs

!!! quote "The central question it answers"
    _"Can I prove, right now, that this release is compliant — and here is the evidence?"_

---

## Capabilities at a Glance

| Capability | Description |
|------------|-------------|
| 🗂️ **Requirements Traceability** | Ingest requirements from YAML, link to controls, tests, owners, and releases. Detect gaps. |
| 🔐 **Control Mapping** | Model NIST 800-53 controls, map them to technical evidence, track implementation status. |
| 📦 **Evidence Collection** | Normalize CI/CD artifacts, scan results, deployment logs, and manual uploads. |
| 🔗 **Supply Chain Integrity** | Ingest SBOMs (CycloneDX/SPDX), check provenance, flag unsigned artifacts. |
| 🚦 **Release Policy Gates** | Evaluate configurable YAML policy rules before every release. Block on critical failures. |
| 📋 **Audit Export** | Generate downloadable JSON and Markdown audit packages with a full evidence index. |
| ⚠️ **Incident & Exception Linkage** | Attach incidents and risk exceptions to controls, systems, and releases. |
| 🖥️ **CLI & REST API** | Both a FastAPI REST API and a Typer CLI with rich terminal output. |

---

## Quick Navigation

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Getting Started](getting-started/quickstart.md)**

    Up and running in under 5 minutes with Docker Compose.

-   :material-architecture: **[Architecture](architecture.md)**

    Service design, data flow, and component overview.

-   :material-api: **[API Reference](api-reference.md)**

    Full REST API endpoint documentation.

-   :material-shield-check: **[Policy Engine](policy-engine.md)**

    Configure and enforce custom compliance rules.

-   :material-file-document: **[Audit Bundles](audit-bundles.md)**

    Generate tamper-evident audit evidence packages.

-   :material-map: **[Roadmap](roadmap.md)**

    Planned features and milestones.

</div>

---

## Repository

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/AerlixConsulting/aerlix-regulated-delivery-control-plane/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![NIST 800-53](https://img.shields.io/badge/NIST-800--53-red.svg)](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
