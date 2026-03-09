# SBOM & Supply-Chain Integrity

The control plane supports ingesting, validating, and storing Software Bill of Materials (SBOM) records linked to releases and evidence items.

## Supported Formats

| Format | Standard | Notes |
|--------|----------|-------|
| CycloneDX JSON | ECMA-424 | Preferred for Kubernetes/container environments |
| SPDX JSON | ISO/IEC 5962 | Preferred for FedRAMP/NIST workflows |

## Generating SBOMs

### Using Syft (recommended)

```bash
# Install Syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Generate CycloneDX SBOM for a container image
syft ghcr.io/aerlixconsulting/aerlix-regulated-delivery-control-plane/api:latest \
    -o cyclonedx-json > sbom.cdx.json

# Generate SPDX SBOM for the Python source
syft dir:. --include-packages python \
    -o spdx-json > sbom.spdx.json
```

### Using the GitHub Actions Workflow

SBOMs are automatically generated on every push to `main` and for every release tag using the `.github/workflows/sbom.yml` workflow. They are attached as release assets.

## Ingesting SBOMs via the API

```bash
curl -X POST http://localhost:8000/api/v1/releases/{release_id}/sbom \
    -H "Content-Type: application/json" \
    -d @sbom.cdx.json
```

## Supply-Chain Attestations

The `sbom.yml` workflow uses [`actions/attest-build-provenance`](https://github.com/actions/attest-build-provenance) to generate SLSA Level 2 provenance attestations for container images published to GHCR.

Attestations can be verified with:

```bash
gh attestation verify oci://ghcr.io/aerlixconsulting/aerlix-regulated-delivery-control-plane/api:v1.0.0 \
    --owner AerlixConsulting
```

## Container Signing with Cosign

All release images are signed using [Cosign](https://github.com/sigstore/cosign) with keyless OIDC signing via GitHub Actions (see `.github/workflows/cosign.yml`).

### Verifying a Signed Image

```bash
cosign verify \
    --certificate-identity-regexp "https://github.com/AerlixConsulting/aerlix-regulated-delivery-control-plane/.*" \
    --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
    ghcr.io/aerlixconsulting/aerlix-regulated-delivery-control-plane/api:v1.0.0
```

## Policy Gate: SBOM Required

To enforce that all releases have an associated SBOM, add the following rule to your `policy-rules.yaml`:

```yaml
rules:
  - id: RULE-SBOM-001
    name: "All releases must have an SBOM"
    category: supply-chain
    severity: critical
    blocking: true
    condition:
      type: release_has_sbom
      threshold: 1.0
```
