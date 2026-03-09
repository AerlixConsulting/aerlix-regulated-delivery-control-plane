# Quickstart

Get the Aerlix Regulated Delivery Control Plane running locally in under 5 minutes.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 26.0
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.27
- Git

## 1. Clone and Configure

```bash
git clone https://github.com/AerlixConsulting/aerlix-regulated-delivery-control-plane.git
cd aerlix-regulated-delivery-control-plane
cp .env.example .env
```

Edit `.env` to set a strong `SECRET_KEY` before running in any shared environment.

## 2. Start All Services

```bash
make up
# equivalent: docker compose up -d
```

This starts:

| Container | Port | Description |
|-----------|------|-------------|
| `aerlix_api` | 8000 | FastAPI REST API |
| `aerlix_frontend` | 3000 | React dashboard |
| `aerlix_db` | 5432 | PostgreSQL 16 |
| `aerlix_redis` | 6379 | Redis 7 |
| `aerlix_pgadmin` | 5050 | pgAdmin (optional) |

## 3. Seed Demo Data

```bash
make seed-db
# equivalent: docker compose exec api python -m sample_data.seed_db
```

## 4. Explore

| Service | URL |
|---------|-----|
| **Dashboard** | <http://localhost:3000> |
| **API Docs (Swagger)** | <http://localhost:8000/docs> |
| **API Docs (ReDoc)** | <http://localhost:8000/redoc> |
| **pgAdmin** | <http://localhost:5050> |

## 5. Run the CLI

```bash
# Using the installed script (if using Poetry)
poetry run aerlix --help

# Or via Docker
docker compose exec api aerlix --help
```

## Next Steps

- [Configure environment variables](configuration.md)
- [Run the demo walkthrough](../demo-walkthrough.md)
- [Explore the API reference](../api-reference.md)
