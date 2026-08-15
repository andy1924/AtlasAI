"""
CloudGuard — FastAPI Application Entry Point

Architecture:
  Telemetry → /api/events (POST) → Detection Pipeline → Incidents → Dashboard
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.health import router as health_router
from app.api.events import router as events_router
from app.api.containers import router as containers_router
from app.api.incidents import router as incidents_router
from app.api.analytics import router as analytics_router
from app.api.demo import router as demo_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cloudguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info("CloudGuard starting up...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"Demo mode: {settings.DEMO_MODE_ENABLED}")

    # Initialize database tables
    await init_db()
    logger.info("Database initialized ✓")

    yield

    logger.info("CloudGuard shutting down...")


# ─── FastAPI Application ──────────────────────────────────────────────────────

app = FastAPI(
    title="CloudGuard API",
    description=(
        "AI-Assisted Cloud-Native Runtime Threat Detection & Automated Response Platform. "
        "Detects threats via rule-based engine + ML anomaly detection, "
        "correlates events into incidents, and supports automated response."
    ),
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ─── Global Exception Handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )

# ─── Routers ─────────────────────────────────────────────────────────────────
PREFIX = settings.API_PREFIX

app.include_router(health_router, prefix=PREFIX)
app.include_router(events_router, prefix=PREFIX)
app.include_router(containers_router, prefix=PREFIX)
app.include_router(incidents_router, prefix=PREFIX)
app.include_router(analytics_router, prefix=PREFIX)
app.include_router(demo_router, prefix=PREFIX)

# ─── Root redirect ────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/api/health",
    }
