"""Analytics API — aggregate stats for the dashboard."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.core.database import get_db
from app.models.container import Container
from app.models.event import RuntimeEvent
from app.models.incident import Incident
from app.schemas import AnalyticsSummary

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsSummary, tags=["Analytics"])
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """
    Aggregate analytics for the SOC dashboard.
    All numbers come from the real database — no hardcoded values.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Container counts
    total_containers_r = await db.execute(select(func.count(Container.id)))
    total_containers = total_containers_r.scalar() or 0

    active_containers_r = await db.execute(
        select(func.count(Container.id)).where(Container.status == "running")
    )
    active_containers = active_containers_r.scalar() or 0

    # Incident counts
    open_incidents_r = await db.execute(
        select(func.count(Incident.id)).where(Incident.status.in_(["OPEN", "INVESTIGATING"]))
    )
    open_incidents = open_incidents_r.scalar() or 0

    critical_incidents_r = await db.execute(
        select(func.count(Incident.id)).where(
            and_(Incident.severity == "CRITICAL", Incident.status.in_(["OPEN", "INVESTIGATING"]))
        )
    )
    critical_incidents = critical_incidents_r.scalar() or 0

    # High-risk containers (risk_score > 50)
    high_risk_r = await db.execute(
        select(func.count(Container.id)).where(Container.risk_score > 50)
    )
    high_risk_containers = high_risk_r.scalar() or 0

    # Threats today
    threats_today_r = await db.execute(
        select(func.count(Incident.id)).where(Incident.created_at >= today_start)
    )
    threats_today = threats_today_r.scalar() or 0

    # Total events
    total_events_r = await db.execute(select(func.count(RuntimeEvent.id)))
    total_events = total_events_r.scalar() or 0

    # Detection rate (incidents per event, if any events)
    total_incidents_r = await db.execute(select(func.count(Incident.id)))
    total_incidents = total_incidents_r.scalar() or 0
    detection_rate = round(total_incidents / total_events, 4) if total_events > 0 else 0.0

    # Avg risk score
    avg_risk_r = await db.execute(select(func.avg(Incident.risk_score)))
    avg_risk = round(avg_risk_r.scalar() or 0.0, 1)

    # Events by type (top 10)
    events_by_type_r = await db.execute(
        select(RuntimeEvent.event_type, func.count(RuntimeEvent.id).label("count"))
        .group_by(RuntimeEvent.event_type)
        .order_by(desc("count"))
        .limit(10)
    )
    events_by_type = {row[0]: row[1] for row in events_by_type_r.fetchall()}

    # Incidents by severity
    incidents_by_sev_r = await db.execute(
        select(Incident.severity, func.count(Incident.id).label("count"))
        .group_by(Incident.severity)
    )
    incidents_by_severity = {row[0]: row[1] for row in incidents_by_sev_r.fetchall()}

    # Incidents by status
    incidents_by_status_r = await db.execute(
        select(Incident.status, func.count(Incident.id).label("count"))
        .group_by(Incident.status)
    )
    incidents_by_status = {row[0]: row[1] for row in incidents_by_status_r.fetchall()}

    # Recent threats (last 10)
    recent_r = await db.execute(
        select(Incident).order_by(desc(Incident.created_at)).limit(10)
    )
    recent_incidents = recent_r.scalars().all()
    recent_threats = [
        {
            "id": inc.id,
            "incident_number": inc.incident_number,
            "title": inc.title,
            "severity": inc.severity,
            "risk_score": inc.risk_score,
            "status": inc.status,
            "container_name": inc.container_name,
            "created_at": inc.created_at.isoformat(),
        }
        for inc in recent_incidents
    ]

    return AnalyticsSummary(
        total_containers=total_containers,
        active_containers=active_containers,
        open_incidents=open_incidents,
        critical_incidents=critical_incidents,
        high_risk_containers=high_risk_containers,
        threats_today=threats_today,
        total_events=total_events,
        detection_rate=detection_rate,
        avg_risk_score=avg_risk,
        events_by_type=events_by_type,
        incidents_by_severity=incidents_by_severity,
        incidents_by_status=incidents_by_status,
        recent_threats=recent_threats,
    )


@router.get("/threats", tags=["Analytics"])
async def list_threats(db: AsyncSession = Depends(get_db)):
    """Latest threats for the live feed."""
    result = await db.execute(
        select(Incident).order_by(desc(Incident.created_at)).limit(100)
    )
    incidents = result.scalars().all()
    return [
        {
            "id": inc.id,
            "incident_number": inc.incident_number,
            "title": inc.title,
            "severity": inc.severity,
            "risk_score": round(inc.risk_score, 1),
            "status": inc.status,
            "container_name": inc.container_name,
            "container_id": inc.container_id,
            "detection_rule": inc.detection_rule,
            "mitre_technique": inc.mitre_technique,
            "mitre_technique_id": inc.mitre_technique_id,
            "first_seen": inc.first_seen.isoformat(),
            "last_seen": inc.last_seen.isoformat(),
            "created_at": inc.created_at.isoformat(),
        }
        for inc in incidents
    ]
