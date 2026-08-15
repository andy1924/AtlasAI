"""Incidents API — query and manage security incidents."""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.core.database import get_db
from app.models.incident import Incident
from app.models.detection import Detection, ResponseAction
from app.schemas import IncidentResponse, DetectionResponse, ResponseActionResponse

router = APIRouter()


@router.get("/incidents", response_model=List[IncidentResponse], tags=["Incidents"])
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    container_id: Optional[str] = Query(None),
):
    """List security incidents with optional filters."""
    stmt = select(Incident).order_by(desc(Incident.created_at))

    if status:
        stmt = stmt.where(Incident.status == status.upper())
    if severity:
        stmt = stmt.where(Incident.severity == severity.upper())
    if container_id:
        stmt = stmt.where(Incident.container_id == container_id)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific incident by ID."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/incidents/{incident_id}/acknowledge", tags=["Incidents"])
async def acknowledge_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an incident as acknowledged / being investigated."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "INVESTIGATING"
    incident.acknowledged_at = datetime.now(timezone.utc)
    incident.acknowledged_by = "analyst"
    incident.updated_at = datetime.now(timezone.utc)
    return {"message": "Incident acknowledged", "status": incident.status}


@router.post("/incidents/{incident_id}/resolve", tags=["Incidents"])
async def resolve_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an incident as resolved."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "RESOLVED"
    incident.resolved_at = datetime.now(timezone.utc)
    incident.updated_at = datetime.now(timezone.utc)
    return {"message": "Incident resolved", "status": incident.status}


@router.post("/incidents/{incident_id}/false-positive", tags=["Incidents"])
async def mark_false_positive(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an incident as a false positive."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "FALSE_POSITIVE"
    incident.updated_at = datetime.now(timezone.utc)
    return {"message": "Marked as false positive", "status": incident.status}


@router.get("/incidents/{incident_id}/detections", response_model=List[DetectionResponse], tags=["Incidents"])
async def get_incident_detections(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get all detection records associated with an incident."""
    result = await db.execute(
        select(Detection).where(Detection.incident_id == incident_id)
        .order_by(Detection.created_at)
    )
    return result.scalars().all()


@router.get("/incidents/{incident_id}/response-actions", response_model=List[ResponseActionResponse], tags=["Incidents"])
async def get_incident_response_actions(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get all response actions taken for an incident."""
    result = await db.execute(
        select(ResponseAction).where(ResponseAction.incident_id == incident_id)
        .order_by(ResponseAction.created_at)
    )
    return result.scalars().all()
