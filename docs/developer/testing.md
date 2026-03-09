# Testing Guide

## Test Framework

The project uses **pytest** with **pytest-asyncio** for async test support and **pytest-cov** for coverage.

## Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run a specific file
pytest tests/test_traceability.py -v

# Run tests matching a pattern
pytest -k "test_coverage" -v
```

## Test Configuration

Test settings are in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=app --cov-report=term-missing --cov-report=xml"
```

## Test Database

Tests use **SQLite in-memory** (`sqlite+aiosqlite:///:memory:`) — no external services required. The `conftest.py` creates a fresh database schema for each test function and tears it down after.

## Test Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `db_session` | `function` | Fresh async SQLAlchemy session per test |
| `client` | `function` | HTTPX async test client with DB override |

## Coverage Targets

| Module | Target |
|--------|--------|
| `app/services/` | ≥ 90% |
| `app/api/v1/` | ≥ 80% |
| `app/models/` | ≥ 70% |

## CI Integration

Tests run automatically on every push and PR via `.github/workflows/test.yml`. Coverage reports are uploaded to Codecov.
