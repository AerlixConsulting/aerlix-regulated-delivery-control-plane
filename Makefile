.PHONY: help install dev-install up down logs shell test lint type-check fmt seed-db generate-audit demo

PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker compose
APP_NAME := aerlix-control-plane

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

dev-install: ## Install all dependencies including dev tools
	$(PIP) install -e ".[dev]" || $(PIP) install -r requirements.txt
	pre-commit install

up: ## Start all services with docker-compose
	$(DOCKER_COMPOSE) up -d
	@echo ""
	@echo "✅ Aerlix Control Plane is running"
	@echo "   API:      http://localhost:8000"
	@echo "   Docs:     http://localhost:8000/docs"
	@echo "   Frontend: http://localhost:3000"
	@echo "   PgAdmin:  http://localhost:5050"

down: ## Stop all services
	$(DOCKER_COMPOSE) down

logs: ## Follow logs from all containers
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Follow API server logs
	$(DOCKER_COMPOSE) logs -f api

shell: ## Open shell in running API container
	$(DOCKER_COMPOSE) exec api bash

db-shell: ## Open psql in the database container
	$(DOCKER_COMPOSE) exec db psql -U aerlix -d aerlix_control_plane

test: ## Run test suite
	pytest tests/ -v --cov=app --cov-report=term-missing

test-ci: ## Run tests for CI (no cov report)
	pytest tests/ -v

lint: ## Lint Python code with ruff
	ruff check app/ tests/ sample_data/
	@echo "✅ Lint passed"

fmt: ## Format Python code with ruff
	ruff format app/ tests/ sample_data/
	ruff check --fix app/ tests/ sample_data/

type-check: ## Type-check with mypy
	mypy app/ --ignore-missing-imports

seed-db: ## Seed demo data into the database
	$(PYTHON) -m sample_data.seed_db
	@echo "✅ Demo database seeded"

ingest-requirements: ## Ingest sample requirements from YAML
	aerlix ingest-requirements examples/requirements.yaml

ingest-controls: ## Ingest sample controls from YAML
	aerlix ingest-controls examples/controls.yaml

ingest-evidence: ## Ingest sample evidence from JSON
	aerlix ingest-evidence examples/evidence.json

evaluate-release: ## Evaluate release readiness
	aerlix evaluate-release --release-id REL-001

generate-audit: ## Generate audit bundle
	aerlix generate-audit-bundle --output /tmp/audit-bundle.json
	@echo "✅ Audit bundle written to /tmp/audit-bundle.json"

demo: up ## Full one-command demo setup
	@echo "⏳ Waiting for services to be ready..."
	sleep 5
	$(DOCKER_COMPOSE) exec api python -m sample_data.seed_db
	@echo ""
	@echo "🎉 Demo environment ready!"
	@echo "   API Docs:  http://localhost:8000/docs"
	@echo "   Dashboard: http://localhost:3000"

build-docker: ## Build Docker images
	$(DOCKER_COMPOSE) build

clean: ## Remove Python bytecode and test artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type d -name "*.egg-info" -delete
	rm -f coverage.xml .coverage
	@echo "✅ Cleaned"

precommit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

migrate: ## Run database migrations
	alembic upgrade head

migration-new: ## Create a new Alembic migration (usage: make migration-new MSG="add table")
	alembic revision --autogenerate -m "$(MSG)"
