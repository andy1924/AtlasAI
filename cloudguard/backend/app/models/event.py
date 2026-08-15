"""CloudGuard ORM Models — RuntimeEvent (Normalized Event Schema)"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class RuntimeEvent(Base):
    """
    Unified normalized event schema.
    All telemetry sources (Falco, simulated, eBPF) are normalized into this schema.
    """
    __tablename__ = "runtime_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Core identity
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    # e.g. PROCESS_EXEC, PROCESS_EXIT, NET_CONNECT, FILE_CREATE, FILE_MODIFY,
    #      FILE_DELETE, CONTAINER_CREATE, PRIV_CHANGE, SHELL_EXEC

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=utcnow)

    # Container context
    container_id: Mapped[str] = mapped_column(String(128), ForeignKey("containers.container_id"), index=True, nullable=True)
    container_name: Mapped[str] = mapped_column(String(256), nullable=True)
    host: Mapped[str] = mapped_column(String(256), default="localhost")

    # Process fields
    process_name: Mapped[str] = mapped_column(String(512), nullable=True)
    process_pid: Mapped[int] = mapped_column(Integer, nullable=True)
    parent_process: Mapped[str] = mapped_column(String(512), nullable=True)
    parent_pid: Mapped[int] = mapped_column(Integer, nullable=True)
    command_line: Mapped[str] = mapped_column(Text, nullable=True)
    user: Mapped[str] = mapped_column(String(256), nullable=True)
    user_uid: Mapped[int] = mapped_column(Integer, nullable=True)

    # Network fields
    source_ip: Mapped[str] = mapped_column(String(64), nullable=True)
    source_port: Mapped[int] = mapped_column(Integer, nullable=True)
    destination_ip: Mapped[str] = mapped_column(String(64), nullable=True)
    destination_port: Mapped[int] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str] = mapped_column(String(16), nullable=True)  # TCP, UDP, ICMP
    bytes_sent: Mapped[int] = mapped_column(Integer, nullable=True)
    bytes_received: Mapped[int] = mapped_column(Integer, nullable=True)

    # File fields
    file_path: Mapped[str] = mapped_column(String(1024), nullable=True)
    file_operation: Mapped[str] = mapped_column(String(64), nullable=True)  # read, write, delete, create

    # Severity
    severity: Mapped[str] = mapped_column(String(16), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL

    # Telemetry source
    source: Mapped[str] = mapped_column(String(64), default="simulated")  # simulated, falco, ebpf

    # Raw event payload (for audit/debugging)
    raw_event: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    container_rel = relationship("Container", back_populates="events", foreign_keys=[container_id])
    detections = relationship("Detection", back_populates="event", lazy="select")
