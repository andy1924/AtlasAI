from typing import List, Annotated, TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import AnyMessage, add_messages


# --- Pydantic Models for Data Validation ---

class Shipment(BaseModel):
    shipment_id: str
    origin: str
    destination: str
    carrier: str
    weight_kg: float
    distance_km: float
    eta_hours: int
    status: str
    delay_probability: float
    operational_cost: float
    partner_reliability: float
    timestamp: str


class Alert(BaseModel):
    id: str
    type: str = Field(description="e.g., 'Port Strike', 'Weather Delay', 'Piracy'")
    location: str
    severity: str = Field(description="'High', 'Medium', 'Low'")
    description: str


class CarrierStats(BaseModel):
    """Tracks live carrier performance across all shipments."""
    carrier: str
    total_shipments: int = 0
    delayed_shipments: int = 0
    reliability_score: float = 1.0  # 1.0 = perfect, 0.0 = all delayed


# --- LangGraph State Definition ---

class AgentState(TypedDict):
    # Message history — add_messages appends, never overwrites
    messages: Annotated[list[AnyMessage], add_messages]

    # Environment data (Observe phase)
    shipments: List[Shipment]
    alerts: List[Alert]

    # Agent's internal reasoning
    hypothesis: str           # Populated by Reason node
    decision: str             # Populated by Decide node
    action_taken: str         # Populated by Act node

    # NEW: richer decision metadata for judging & UI
    confidence: int           # 0-100 — how confident agent is in its decision
    action_type: str          # REROUTE | HOLD | SWITCH_CARRIER | EXPEDITE | ESCALATE | MONITOR
    severity_level: str       # Highest severity seen this cycle: High / Medium / Low