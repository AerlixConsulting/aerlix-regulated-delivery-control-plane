# Copilot Instructions for aerlix-regulated-delivery-control-plane

## Repository Overview

This is a **compliance-native software delivery control plane** for regulated environments. It links requirements, NIST-aligned controls, CI/CD evidence, SBOM and supply-chain integrity, and policy-based release gates. It generates traceability graphs and audit-ready evidence bundles.

**Domain concepts:**
- **Requirements** – formal delivery requirements traceable to controls and evidence
- **Controls** – NIST SP 800-53 / FedRAMP-aligned security and compliance controls
- **Evidence** – CI/CD artifacts, test results, SBOM, and scan reports linked to controls
- **Release gates** – policy rules that must pass before a release is approved
- **Traceability graph** – directed graph connecting requirements → controls → evidence → releases
- **Audit bundle** – exportable, tamper-evident archive of traceability evidence for auditors

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11+, FastAPI, Uvicorn |
| ORM | SQLAlchemy (async), Alembic for migrations |
| Validation | Pydantic v2 |
| CLI | Typer |
| Dependency management | Poetry (`pyproject.toml`) + `requirements.txt` |
| Database | PostgreSQL (production), SQLite (development/testing) |
| Frontend | React 18, TypeScript, Vite, React Router |
| Containerisation | Docker, Docker Compose |
| Testing | Pytest, pytest-asyncio, HTTPX (async test client) |
| Linting / formatting | Ruff (lint + format), mypy (type checking) |
| Pre-commit hooks | `.pre-commit-config.yaml` |
| CI/CD | GitHub Actions (`.github/workflows/`) |

## Project Layout

```
.
├── app/                        # FastAPI backend
│   ├── core/
│   │   └── config.py           # Settings via pydantic-settings
│   ├── db.py                   # SQLAlchemy async engine + session factory
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Business logic
│   │   ├── traceability.py     # Traceability graph engine
│   │   ├── policy_engine.py    # Release-gate policy evaluation
│   │   └── audit_exporter.py   # Audit bundle generation
│   ├── api/
│   │   └── v1/                 # Versioned REST endpoints
│   │       ├── requirements.py
│   │       ├── controls.py
│   │       ├── evidence.py
│   │       ├── releases.py
│   │       ├── traceability.py
│   │       ├── policies.py
│   │       └── audit.py
│   ├── cli/
│   │   └── main.py             # Typer CLI entry point
│   └── main.py                 # FastAPI app factory
├── frontend/                   # React/TypeScript SPA
│   ├── src/
│   │   ├── components/         # Shared UI components
│   │   └── pages/              # Route-level page components
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
├── tests/                      # Pytest test suite
│   ├── conftest.py             # Shared fixtures (DB, client)
│   ├── test_traceability.py
│   └── test_policy_engine.py
├── docs/                       # Markdown documentation
├── examples/                   # Sample YAML/JSON data files
├── sample_data/
│   └── seed_db.py              # Database seeding script
├── .github/
│   ├── copilot-instructions.md # This file
│   └── workflows/
│       ├── test.yml            # CI: lint, type-check, test
│       └── build.yml           # CI: Docker build and push
├── pyproject.toml              # Poetry config, tool settings (ruff, mypy, pytest)
├── requirements.txt            # pip-installable dependencies
├── Makefile                    # Developer convenience targets
├── Dockerfile                  # Backend container image
├── docker-compose.yml          # Full-stack local environment
└── .env.example                # Environment variable template
```

## Bootstrap and Build

### Python backend

```bash
# Install dependencies (always run after pulling changes)
poetry install

# Or using pip
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server (development)
uvicorn app.main:app --reload --port 8000

# Start via Docker Compose (full stack: API + DB + frontend)
docker-compose up --build
```

### Frontend

```bash
cd frontend
npm install       # always run before building or starting dev server
npm run dev       # start Vite dev server on http://localhost:5173
npm run build     # production build to frontend/dist/
npm run preview   # serve the production build locally
```

## Testing

```bash
# Run all backend tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_traceability.py -v

# Run frontend tests (if configured)
cd frontend && npm test
```

The test database uses SQLite in-memory mode configured in `tests/conftest.py`. No external services are required to run the test suite.

## Linting and Type Checking

```bash
# Lint and auto-fix with Ruff
ruff check . --fix
ruff format .

# Type checking
mypy app/

# Run all pre-commit hooks (equivalent to CI lint step)
pre-commit run --all-files
```

Ruff and mypy configuration lives in `pyproject.toml` under `[tool.ruff]` and `[tool.mypy]`.

## Key Architectural Patterns

- **API versioning**: all endpoints live under `/api/v1/`. Add new versions as `/api/v2/` etc.
- **Service layer**: business logic belongs in `app/services/`, not in route handlers.
- **Async-first**: use `async def` for route handlers and service methods; use `AsyncSession` for DB access.
- **Pydantic schemas**: request bodies use `Create`-suffixed schemas; responses use plain name schemas (e.g. `ControlCreate` vs `Control`).
- **Policy evaluation**: the `policy_engine.py` service evaluates release-gate rules against the current traceability graph state; policies are stored as YAML rule sets.
- **Audit bundles**: generated as signed JSON archives by `audit_exporter.py`; include the full traceability graph snapshot, evidence hashes, and release gate decisions.

## CI/CD Workflows

- **`test.yml`** – triggered on every push and PR: installs dependencies, runs `pre-commit`, `mypy`, and `pytest`.
- **`build.yml`** – triggered on pushes to `main` and version tags: builds and pushes the Docker image.

Always ensure `pytest` and `ruff check .` pass locally before pushing. The CI will fail on lint errors or type errors.

## Environment Variables

Copy `.env.example` to `.env` before running locally. Key variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLAlchemy connection string |
| `SECRET_KEY` | App secret for signing tokens/bundles |
| `ENVIRONMENT` | `development` \| `production` |
| `LOG_LEVEL` | Logging verbosity |

## Trust These Instructions

Trust the information in this file. Only search the codebase if the information here appears incomplete or incorrect. The layout, commands, and patterns documented above reflect the intended design of this repository.
