"""
CloudGuard Event Service

Handles event ingestion, normalization, and detection pipeline orchestration.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.models.event import RuntimeEvent
from app.models.incident import Incident
from app.models.detection import Detection, ResponseAction, AuditLog
from app.models.container import Container
from app.schemas import EventIngest
from app.detection.rules import (
    rule_suspicious_shell,
    rule_reverse_shell,
    rule_privilege_escalation,
    rule_suspicious_external_connection,
    rule_cryptomining,
    rule_rapid_file_modification,
)
from app.detection.risk_engine import calculate_risk


async def ingest_event(db: AsyncSession, event_data: EventIngest) -> RuntimeEvent:
    """
    Ingest a runtime event, run detection rules, and create incidents as needed.
    This is the main entry point for the detection pipeline.
    """
    # 1. Ensure container exists in registry before event insertion (Foreign Key constraint)
    await ensure_container(db, event_data)

    # 2. Create normalized RuntimeEvent record
    event = RuntimeEvent(
        id=str(uuid.uuid4()),
        event_type=event_data.event_type,
        timestamp=event_data.timestamp or datetime.now(timezone.utc),
        container_id=event_data.container_id,
        container_name=event_data.container_name,
        host=event_data.host,
        process_name=event_data.process_name,
        process_pid=event_data.process_pid,
        parent_process=event_data.parent_process,
        parent_pid=event_data.parent_pid,
        command_line=event_data.command_line,
        user=event_data.user,
        user_uid=event_data.user_uid,
        source_ip=event_data.source_ip,
        source_port=event_data.source_port,
        destination_ip=event_data.destination_ip,
        destination_port=event_data.destination_port,
        protocol=event_data.protocol,
        bytes_sent=event_data.bytes_sent,
        bytes_received=event_data.bytes_received,
        file_path=event_data.file_path,
        file_operation=event_data.file_operation,
        severity=event_data.severity,
        source=event_data.source,
        raw_event=event_data.raw_event,
    )
    db.add(event)
    await db.flush()  # get the ID without committing

    # 3. Run rule-based detection
    await run_detection_pipeline(db, event)

    return event


async def ensure_container(db: AsyncSession, event_data: EventIngest) -> Optional[Container]:
    """Register container if not seen before."""
    if not event_data.container_id:
        return None

    result = await db.execute(
        select(Container).where(Container.container_id == event_data.container_id)
    )
    container = result.scalar_one_or_none()

    if not container:
        container = Container(
            id=str(uuid.uuid4()),
            container_id=event_data.container_id,
            name=event_data.container_name or event_data.container_id,
            host=event_data.host,
            status="running",
        )
        db.add(container)
    else:
        container.last_seen = datetime.now(timezone.utc)
        if event_data.container_name:
            container.name = event_data.container_name

    return container


async def run_detection_pipeline(db: AsyncSession, event: RuntimeEvent) -> None:
    """
    Run all detection rules against the event and create incidents for matches.
    """
    # Context: check if recent shell was seen in same container (for RULE-002)
    recent_shell = False
    if event.container_id:
        window_start = datetime.now(timezone.utc) - timedelta(minutes=5)
        shell_result = await db.execute(
            select(func.count(RuntimeEvent.id)).where(
                and_(
                    RuntimeEvent.container_id == event.container_id,
                    RuntimeEvent.event_type.in_(["SHELL_EXEC", "PROCESS_EXEC"]),
                    RuntimeEvent.process_name.in_(["bash", "sh", "zsh", "ash"]),
                    RuntimeEvent.timestamp >= window_start,
                )
            )
        )
        recent_shell = (shell_result.scalar() or 0) > 0

    # Get file mod rate for RULE-006
    file_mod_rate = 0.0
    if event.container_id and event.event_type in ("FILE_MODIFY", "FILE_DELETE", "FILE_CREATE"):
        window_start = datetime.now(timezone.utc) - timedelta(minutes=1)
        mod_result = await db.execute(
            select(func.count(RuntimeEvent.id)).where(
                and_(
                    RuntimeEvent.container_id == event.container_id,
                    RuntimeEvent.event_type.in_(["FILE_MODIFY", "FILE_DELETE", "FILE_CREATE"]),
                    RuntimeEvent.timestamp >= window_start,
                )
            )
        )
        file_mod_rate = float(mod_result.scalar() or 0)

    # Run each rule
    results = [
        rule_suspicious_shell(event),
        rule_reverse_shell(event, recent_shell_in_container=recent_shell),
        rule_privilege_escalation(event),
        rule_suspicious_external_connection(event),
        rule_cryptomining(event),
        rule_rapid_file_modification(event, file_mod_rate_per_minute=file_mod_rate),
    ]

    triggered = [r for r in results if r.triggered]
    if not triggered:
        return

    # Calculate risk score
    risk = calculate_risk(
        rule_results=triggered,
        correlated_event_count=1,
    )

    # Find the highest-severity triggered rule for incident title
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    top_rule = max(triggered, key=lambda r: severity_order.get(r.severity, 0))

    # Create or update incident
    incident = await get_or_create_incident(db, event, top_rule, risk, triggered)

    # Save detection records
    for rule_result in triggered:
        detection = Detection(
            id=str(uuid.uuid4()),
            event_id=event.id,
            incident_id=incident.id,
            detection_type="RULE",
            rule_name=rule_result.rule_name,
            rule_id=rule_result.rule_id,
            confidence=rule_result.confidence,
            severity=rule_result.severity,
            risk_score=rule_result.risk_contribution,
            explanation=rule_result.explanation,
            matched_indicators=rule_result.indicators,
            mitre_technique=rule_result.mitre_technique,
            mitre_technique_id=rule_result.mitre_technique_id,
            container_id=event.container_id,
        )
        db.add(detection)

    # Update container risk
    if event.container_id:
        result = await db.execute(
            select(Container).where(Container.container_id == event.container_id)
        )
        container = result.scalar_one_or_none()
        if container:
            container.risk_score = max(container.risk_score, risk.capped_score)
            container.threat_count += 1


async def get_or_create_incident(
    db: AsyncSession, event: RuntimeEvent, top_rule, risk, all_triggered
) -> Incident:
    """
    Find an existing open incident for this container/rule, or create a new one.
    """
    # Look for an open incident for this container in the last 15 minutes
    if event.container_id:
        window = datetime.now(timezone.utc) - timedelta(minutes=15)
        result = await db.execute(
            select(Incident).where(
                and_(
                    Incident.container_id == event.container_id,
                    Incident.status.in_(["OPEN", "INVESTIGATING"]),
                    Incident.detection_rule == top_rule.rule_id,
                    Incident.created_at >= window,
                )
            ).order_by(desc(Incident.created_at)).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.last_seen = datetime.now(timezone.utc)
            existing.risk_score = max(existing.risk_score, risk.capped_score)
            existing.updated_at = datetime.now(timezone.utc)
            return existing

    # Get next incident number
    count_result = await db.execute(select(func.count(Incident.id)))
    incident_number = (count_result.scalar() or 0) + 1

    all_indicators = []
    for r in all_triggered:
        all_indicators.extend(r.indicators)

    all_actions = []
    for r in all_triggered:
        all_actions.extend(r.recommended_actions)

    incident = Incident(
        id=str(uuid.uuid4()),
        incident_number=incident_number,
        title=f"{top_rule.rule_name} — {event.container_name or event.container_id or 'Unknown Container'}",
        description=(
            f"Detection rule '{top_rule.rule_name}' triggered on container "
            f"'{event.container_name or event.container_id}'. "
            f"{top_rule.explanation}"
        ),
        severity=top_rule.severity,
        risk_score=risk.capped_score,
        status="OPEN",
        container_id=event.container_id,
        container_name=event.container_name,
        host=event.host,
        detection_rule=top_rule.rule_id,
        mitre_technique=top_rule.mitre_technique,
        mitre_technique_id=top_rule.mitre_technique_id,
        risk_factors=risk.breakdown,
        attack_indicators=all_indicators[:20],  # cap at 20
        recommended_actions=list(dict.fromkeys(all_actions))[:10],  # deduplicated
        evidence={
            "triggering_event_id": event.id,
            "event_type": event.event_type,
            "process_name": event.process_name,
            "command_line": event.command_line,
            "destination_ip": event.destination_ip,
            "destination_port": event.destination_port,
            "file_path": event.file_path,
        },
    )
    db.add(incident)
    await db.flush()
    return incident
