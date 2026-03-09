# Configuration

All configuration is managed via environment variables. Copy `.env.example` to `.env` before starting the stack.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | Async SQLAlchemy connection string (asyncpg driver) |
| `DATABASE_URL_SYNC` | ✅ | — | Synchronous SQLAlchemy URL (for Alembic migrations) |
| `SECRET_KEY` | ✅ | — | 32+ character random string for JWT signing |
| `APP_ENV` | — | `development` | `development` \| `staging` \| `production` |
| `LOG_LEVEL` | — | `info` | `debug` \| `info` \| `warning` \| `error` |
| `REDIS_URL` | — | `redis://localhost:6379/0` | Redis connection URL (for Celery workers) |
| `ALLOWED_ORIGINS` | — | `*` | Comma-separated list of allowed CORS origins |

## Database URL Format

```
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
```

For local development with Docker Compose:

```
DATABASE_URL=postgresql+asyncpg://aerlix:aerlix_dev_password@db:5432/aerlix_control_plane
```

## Secret Key Generation

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Production Checklist

- [ ] `SECRET_KEY` is a cryptographically random string (not the example value)
- [ ] `APP_ENV=production`
- [ ] `ALLOWED_ORIGINS` is restricted to your domain(s)
- [ ] Database uses TLS (`sslmode=require`)
- [ ] Secrets are stored in a secret manager (AWS Secrets Manager, Vault, etc.)
