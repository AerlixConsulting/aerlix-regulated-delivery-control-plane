# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` (latest) | ✅ Active support |
| Tagged releases ≥ v0.5 | ✅ Security fixes backported |
| Tagged releases < v0.5 | ❌ End-of-life |

## Reporting a Vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**

Report security issues by emailing **security@aerlix.io**. Include:

1. A description of the vulnerability
2. Steps to reproduce (with as much detail as possible)
3. The potential impact
4. Any suggested remediation

We will acknowledge your report within **24 hours** and provide a remediation timeline within **5 business days**. We follow [responsible disclosure](https://cheatsheetseries.owasp.org/cheatsheets/Vulnerability_Disclosure_Cheat_Sheet.html) practices.

## Security Measures

This project uses the following automated security tooling:

| Tool | Purpose | Schedule |
|------|---------|----------|
| **CodeQL** | SAST — Python and JavaScript/TypeScript | Push + weekly |
| **Dependabot** | Automated dependency updates | Weekly |
| **Syft** | SBOM generation (SPDX + CycloneDX) | Every `main` push + releases |
| **Cosign** | Container image signing (keyless OIDC) | Every release tag |
| **SLSA Provenance** | Build attestations for release artifacts | Every release tag |
| **Ruff** | Python lint / style enforcement | Every PR |
| **pre-commit** | Secret detection, YAML/JSON validation | Every commit |

## Dependency Updates

Dependabot is configured to open weekly PRs for Python, npm, and GitHub Actions dependencies. Maintainers review and merge these promptly.

## Contact

- **Security reports**: security@aerlix.io
- **General contact**: engineering@aerlix.io
