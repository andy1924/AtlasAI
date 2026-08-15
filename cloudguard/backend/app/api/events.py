"""Events API — ingest and query runtime events."""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.event import RuntimeEvent
from app.schemas import EventIngest, EventResponse
from app.services.event_service import ingest_event

router = APIRouter()


@router.post("/events", response_model=EventResponse, status_code=201, tags=["Events"])
async def ingest_runtime_event(
    event_data: EventIngest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a normalized runtime event into the CloudGuard pipeline.
    Triggers detection rules and creates incidents automatically.
    """
    event = await ingest_event(db, event_data)
    return event


@router.get("/events", response_model=List[EventResponse], tags=["Events"])
async def list_events(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    container_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
):
    """List runtime events with optional filters."""
    stmt = select(RuntimeEvent).order_by(desc(RuntimeEvent.timestamp))

    if container_id:
        stmt = stmt.where(RuntimeEvent.container_id == container_id)
    if event_type:
        stmt = stmt.where(RuntimeEvent.event_type == event_type)
    if severity:
        stmt = stmt.where(RuntimeEvent.severity == severity.upper())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/events/{event_id}", response_model=EventResponse, tags=["Events"])
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific runtime event by ID."""
    result = await db.execute(select(RuntimeEvent).where(RuntimeEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
