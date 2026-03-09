"""Application configuration via pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Aerlix Control Plane"
    app_version: str = "0.2.0"
    app_env: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = (
        "postgresql+asyncpg://aerlix:aerlix_dev_password@localhost:5432/aerlix_control_plane"
    )
    database_url_sync: str = (
        "postgresql://aerlix:aerlix_dev_password@localhost:5432/aerlix_control_plane"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Audit / Export
    audit_bundle_output_dir: str = "/tmp/aerlix-audit-bundles"
    evidence_storage_dir: str = "/tmp/aerlix-evidence"

    # Compliance
    default_compliance_framework: str = "NIST-800-53-Rev5"
    required_control_baseline: str = "moderate"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            import json

            return json.loads(v)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
