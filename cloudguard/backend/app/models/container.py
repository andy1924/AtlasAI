"""CloudGuard ORM Models — Container"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Container(Base):
    __tablename__ = "containers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    container_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    image: Mapped[str] = mapped_column(String(512), default="unknown")
    host: Mapped[str] = mapped_column(String(256), default="localhost")
    status: Mapped[str] = mapped_column(String(32), default="running")  # running, stopped, isolated, terminated

    # Resource metrics (updated by telemetry)
    cpu_percent: Mapped[float] = mapped_column(Float, default=0.0)
    memory_percent: Mapped[float] = mapped_column(Float, default=0.0)
    network_rx_bytes: Mapped[int] = mapped_column(Integer, default=0)
    network_tx_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Risk
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    threat_count: Mapped[int] = mapped_column(Integer, default=0)
    is_privileged: Mapped[bool] = mapped_column(Boolean, default=False)
    is_critical_asset: Mapped[bool] = mapped_column(Boolean, default=False)

    # Source metadata
    namespace: Mapped[str] = mapped_column(String(256), default="default")
    labels: Mapped[str] = mapped_column(Text, default="{}")  # JSON string

    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    events = relationship("RuntimeEvent", back_populates="container_rel", lazy="select")
    incidents = relationship("Incident", back_populates="container_rel", lazy="select")
