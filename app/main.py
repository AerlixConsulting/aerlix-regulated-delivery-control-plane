"""Aerlix Regulated Delivery Control Plane — FastAPI Application."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.db import init_db

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: run setup on startup, cleanup on shutdown."""
    logger.info("🚀 Starting Aerlix Control Plane v%s [%s]", settings.app_version, settings.app_env)
    if settings.app_env in ("development", "testing"):
        await init_db()
        logger.info("✅ Database tables ensured")
    yield
    logger.info("🛑 Aerlix Control Plane shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Compliance-native software delivery control plane linking requirements, "
        "NIST-aligned controls, CI/CD evidence, SBOM and supply-chain integrity, "
        "and policy-based release gates. Generates traceability graphs and audit-ready "
        "evidence bundles for regulated environments."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(api_v1_router, prefix=settings.api_prefix)


@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    return JSONResponse(
        {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.app_env,
        }
    )


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
            "api_prefix": settings.api_prefix,
        }
    )
