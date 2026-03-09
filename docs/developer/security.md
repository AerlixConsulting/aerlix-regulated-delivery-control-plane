# Security Guide

## Reporting Vulnerabilities

**Do not open public issues for security vulnerabilities.**

Please report security issues by email to **security@aerlix.io**. We aim to acknowledge within 24 hours and provide a remediation timeline within 5 business days.

## Security Workflows

### CodeQL (SAST)

Static Application Security Testing runs automatically via `.github/workflows/codeql.yml` on every push and weekly on a schedule. Results are available in the **Security → Code scanning alerts** tab on GitHub.

### Dependabot

Automated dependency updates are configured in `.github/dependabot.yml`. Dependabot opens PRs for:
- Python packages (weekly)
- npm packages (weekly)
- GitHub Actions (weekly)

### SBOM Generation

SBOMs are generated automatically for every `main` branch push and every release using Syft. Both SPDX and CycloneDX formats are produced and attached as release assets.

### Container Signing (Cosign)

All release container images are signed using [Cosign](https://github.com/sigstore/cosign) with keyless OIDC signing. Signatures and build provenance attestations are stored in the container registry alongside the images.

### SLSA Provenance

Build provenance attestations (SLSA Level 2) are generated for release images using `actions/attest-build-provenance`.

## Branch Protection

The `main` branch enforces:
- Required status checks (CI lint, tests)
- No direct pushes (PRs required)
- Signed commits recommended

## Secret Management

- Never commit secrets to the repository
- Use environment variables (`.env` locally, secrets manager in production)
- The `detect-private-key` pre-commit hook helps prevent accidental secret commits
- Rotate `SECRET_KEY` if it is ever exposed
