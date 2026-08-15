"""Health check API."""
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings
from app.schemas import HealthResponse

router = APIRouter()
_start_time = time.time()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    System health check endpoint.
    Returns backend status, database connectivity, and runtime information.
    """
    # Test database connectivity
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database=db_status,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=round(time.time() - _start_time, 2),
    )
