# Docker Compose

The `docker-compose.yml` file provides a complete local development stack.

## Services

```yaml
services:
  db        # PostgreSQL 16
  redis     # Redis 7
  api       # FastAPI backend (hot-reload)
  worker    # Celery task worker
  frontend  # React/Vite dev server
  pgadmin   # pgAdmin 4 (optional)
```

## Common Commands

```bash
# Start all services
make up

# Stop all services
make down

# View API logs
docker compose logs -f api

# Run database migrations
docker compose exec api alembic upgrade head

# Seed demo data
make seed-db

# Open a shell in the API container
docker compose exec api bash

# Run tests inside the container
docker compose exec api pytest -v

# Rebuild images after code changes
docker compose up --build api
```

## Volumes

| Volume | Purpose |
|--------|---------|
| `postgres_data` | PostgreSQL data (persists across restarts) |

## Ports

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| API | 8000 | 8000 |
| Frontend | 3000 | 3000 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| pgAdmin | 5050 | 80 |
