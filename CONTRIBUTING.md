# Contributing to Aerlix Regulated Delivery Control Plane

Thank you for your interest in contributing!

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Install pre-commit hooks: `pre-commit install`
5. Copy `.env.example` to `.env`
6. Start the database: `docker compose up -d db redis`
7. Run migrations: `alembic upgrade head`
8. Run tests: `make test`

## Code Style

- Python: ruff (line length 100), mypy for type checking
- TypeScript: ESLint + Prettier
- Run `make fmt` to auto-format
- Run `make lint` to check

## Pull Request Guidelines

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Write tests for new functionality
3. Run `make test` and `make lint` before pushing
4. Write a clear PR description explaining what changes and why
5. Reference any related issues

## Adding Policy Rules

New condition types can be added in `app/services/policy_engine.py`:
1. Add a new case to `PolicyEngine._check()`
2. Implement `_check_my_condition()` returning `(passed: bool, message: str, details: dict | None)`
3. Add a test in `tests/test_policy_engine.py`
4. Document in `docs/policy-engine.md`

## Adding Evidence Connectors

Evidence connectors should:
1. Produce `EvidenceItemCreate` schema objects
2. Include content hash (SHA-256) of the evidence
3. Set appropriate `evidence_type` and `source_system`
4. Handle idempotent re-ingestion gracefully

## Questions?

Open a GitHub issue or discussion.
