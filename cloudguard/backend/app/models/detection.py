"""CloudGuard ORM Models — Detection, ResponseAction, AuditLog"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Detection(Base):
    """Result of applying a detection rule or ML model to an event."""
    __tablename__ = "detections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))

    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("runtime_events.id"), index=True, nullable=True)
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id"), index=True, nullable=True)

    detection_type: Mapped[str] = mapped_column(String(32))  # RULE, ML, HYBRID
    rule_name: Mapped[str] = mapped_column(String(256), nullable=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=True)

    # Confidence and severity
    confidence: Mapped[float] = mapped_column(Float, default=1.0)  # 0.0–1.0
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    # ML-specific fields
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=True)
    is_anomalous: Mapped[bool] = mapped_column(Boolean, nullable=True)
    model_version: Mapped[str] = mapped_column(String(128), nullable=True)

    # Explanation (for transparency/viva)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    matched_indicators: Mapped[list] = mapped_column(JSON, nullable=True)

    # MITRE ATT&CK
    mitre_technique: Mapped[str] = mapped_column(String(256), nullable=True)
    mitre_technique_id: Mapped[str] = mapped_column(String(64), nullable=True)

    container_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    event = relationship("RuntimeEvent", back_populates="detections")
    incident = relationship("Incident", back_populates="detections")


class ResponseAction(Base):
    """An automated or manual response action taken against an incident."""
    __tablename__ = "response_actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))

    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id"), index=True)
    container_id: Mapped[str] = mapped_column(String(128), nullable=True)

    action_type: Mapped[str] = mapped_column(String(64))
    # LOG, ALERT, BLOCK_CONNECTION, ISOLATE_CONTAINER, TERMINATE_PROCESS,
    # PRESERVE_EVIDENCE, CREATE_INCIDENT

    status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING, EXECUTED, FAILED, SKIPPED, REVERSED

    # Action details
    target: Mapped[str] = mapped_column(String(512), nullable=True)  # what was acted on
    result: Mapped[str] = mapped_column(Text, nullable=True)
    is_automated: Mapped[bool] = mapped_column(Boolean, default=True)
    is_reversible: Mapped[bool] = mapped_column(Boolean, default=True)
    reversed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    executed_by: Mapped[str] = mapped_column(String(256), default="system")
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    incident = relationship("Incident", back_populates="response_actions")


class AuditLog(Base):
    """Immutable audit trail for all system actions (security of CloudGuard itself)."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    actor: Mapped[str] = mapped_column(String(256), default="system")
    action: Mapped[str] = mapped_column(String(256), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS")
