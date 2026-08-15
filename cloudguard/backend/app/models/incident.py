"""CloudGuard ORM Models — Incident"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Incident(Base):
    """
    A security incident groups correlated events into a single actionable alert.
    """
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Human-readable sequential ID (e.g. INC-1042)
    incident_number: Mapped[int] = mapped_column(Integer, autoincrement=True, unique=True)

    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[Text] = mapped_column(Text, nullable=True)

    # Severity and risk
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Status lifecycle
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    # OPEN -> INVESTIGATING -> CONTAINED -> RESOLVED | FALSE_POSITIVE

    # Affected resources
    container_id: Mapped[str] = mapped_column(String(128), ForeignKey("containers.container_id"), nullable=True, index=True)
    container_name: Mapped[str] = mapped_column(String(256), nullable=True)
    host: Mapped[str] = mapped_column(String(256), nullable=True)
    affected_user: Mapped[str] = mapped_column(String(256), nullable=True)

    # Detection metadata
    detection_rule: Mapped[str] = mapped_column(String(256), nullable=True)
    mitre_technique: Mapped[str] = mapped_column(String(256), nullable=True)
    mitre_technique_id: Mapped[str] = mapped_column(String(64), nullable=True)

    # ML data
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=True)
    ml_model_version: Mapped[str] = mapped_column(String(128), nullable=True)

    # Risk score breakdown (JSON for transparency)
    risk_factors: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Evidence and context
    attack_indicators: Mapped[list] = mapped_column(JSON, nullable=True)  # list of indicator strings
    recommended_actions: Mapped[list] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Timeline
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    container_rel = relationship("Container", back_populates="incidents", foreign_keys=[container_id])
    detections = relationship("Detection", back_populates="incident", lazy="select")
    response_actions = relationship("ResponseAction", back_populates="incident", lazy="select")
