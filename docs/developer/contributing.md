# Contributing Guide

Thank you for contributing to the Aerlix Regulated Delivery Control Plane!

## Development Setup

```bash
# Clone the repo
git clone https://github.com/AerlixConsulting/aerlix-regulated-delivery-control-plane.git
cd aerlix-regulated-delivery-control-plane

# Install Python dependencies (Poetry recommended)
poetry install

# Install pre-commit hooks
pre-commit install

# Start the dev stack
make up
```

## Running Tests

```bash
# All tests with coverage
pytest --cov=app --cov-report=term-missing

# Specific test file
pytest tests/test_traceability.py -v

# With detailed output
pytest -v -s
```

## Linting

```bash
# Auto-fix lint issues
ruff check . --fix
ruff format .

# Type checking
mypy app/

# All pre-commit hooks
pre-commit run --all-files
```

## Coding Standards

- **Formatting**: Ruff (line length 100)
- **Types**: All public functions must have type annotations
- **Tests**: New features require unit tests; aim for ≥ 80% coverage on changed modules
- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) format

## Pull Request Process

1. Fork the repository and create a feature branch
2. Make changes and run tests + linting locally
3. Open a PR against `main` using the PR template
4. Request a review from at least one maintainer
5. All CI checks must pass before merge

See also: [CONTRIBUTING.md](https://github.com/AerlixConsulting/aerlix-regulated-delivery-control-plane/blob/main/CONTRIBUTING.md)
