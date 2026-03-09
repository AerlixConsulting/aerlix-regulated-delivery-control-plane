"""Alembic environment configuration for Aerlix Control Plane."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# Alembic Config object providing access to values in alembic.ini
config = context.config

# Set up Python logging using alembic.ini config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models metadata so Alembic can detect schema changes
from app.db import Base  # noqa: E402
from app.models import *  # noqa: F401, E402 – registers all ORM models

target_metadata = Base.metadata

# Read DATABASE_URL from application settings (overrides alembic.ini sqlalchemy.url)
from app.core.config import settings  # noqa: E402

config.set_main_option("sqlalchemy.url", settings.database_url_sync)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script output, no DB connection required)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (requires a live synchronous DB connection)."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),  # type: ignore[arg-type]
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
