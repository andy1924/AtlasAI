"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ─── Common ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    timestamp: datetime
    uptime_seconds: float


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]


# ─── Container ────────────────────────────────────────────────────────────────

class ContainerBase(BaseModel):
    container_id: str
    name: str
    image: str = "unknown"
    host: str = "localhost"
    namespace: str = "default"
    is_privileged: bool = False
    is_critical_asset: bool = False


class ContainerCreate(ContainerBase):
    pass


class ContainerResponse(ContainerBase):
    id: str
    status: str
    cpu_percent: float
    memory_percent: float
    network_rx_bytes: int
    network_tx_bytes: int
    risk_score: float
    threat_count: int
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


# ─── Runtime Events ───────────────────────────────────────────────────────────

class EventIngest(BaseModel):
    """Schema for ingesting a new runtime event (from telemetry sources)."""
    event_type: str = Field(..., description="e.g. PROCESS_EXEC, NET_CONNECT, FILE_MODIFY")
    timestamp: Optional[datetime] = None
    container_id: Optional[str] = None
    container_name: Optional[str] = None
    host: str = "localhost"
    process_name: Optional[str] = None
    process_pid: Optional[int] = None
    parent_process: Optional[str] = None
    parent_pid: Optional[int] = None
    command_line: Optional[str] = None
    user: Optional[str] = None
    user_uid: Optional[int] = None
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    file_path: Optional[str] = None
    file_operation: Optional[str] = None
    severity: str = "LOW"
    source: str = "simulated"
    raw_event: Optional[dict] = None


class EventResponse(BaseModel):
    id: str
    event_type: str
    timestamp: datetime
    container_id: Optional[str]
    container_name: Optional[str]
    host: str
    process_name: Optional[str]
    parent_process: Optional[str]
    user: Optional[str]
    source_ip: Optional[str]
    destination_ip: Optional[str]
    destination_port: Optional[int]
    protocol: Optional[str]
    file_path: Optional[str]
    severity: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Incidents ────────────────────────────────────────────────────────────────

class IncidentResponse(BaseModel):
    id: str
    incident_number: int
    title: str
    description: Optional[str]
    severity: str
    risk_score: float
    status: str
    container_id: Optional[str]
    container_name: Optional[str]
    host: Optional[str]
    detection_rule: Optional[str]
    mitre_technique: Optional[str]
    mitre_technique_id: Optional[str]
    anomaly_score: Optional[float]
    risk_factors: Optional[dict]
    attack_indicators: Optional[list]
    recommended_actions: Optional[list]
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Detections ───────────────────────────────────────────────────────────────

class DetectionResponse(BaseModel):
    id: str
    event_id: Optional[str]
    incident_id: Optional[str]
    detection_type: str
    rule_name: Optional[str]
    confidence: float
    severity: str
    risk_score: float
    anomaly_score: Optional[float]
    explanation: Optional[str]
    mitre_technique: Optional[str]
    mitre_technique_id: Optional[str]
    container_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Response Actions ─────────────────────────────────────────────────────────

class ResponseActionResponse(BaseModel):
    id: str
    incident_id: str
    container_id: Optional[str]
    action_type: str
    status: str
    target: Optional[str]
    result: Optional[str]
    is_automated: bool
    executed_by: str
    executed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Analytics ───────────────────────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    total_containers: int
    active_containers: int
    open_incidents: int
    critical_incidents: int
    high_risk_containers: int
    threats_today: int
    total_events: int
    detection_rate: float  # incidents / total events
    avg_risk_score: float
    events_by_type: dict
    incidents_by_severity: dict
    incidents_by_status: dict
    recent_threats: List[dict]
