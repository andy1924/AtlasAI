from typing import List, Annotated, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import AnyMessage, add_messages


# --- Pydantic Models for Data Validation ---

class Shipment(BaseModel):
    id: str
    origin: str
    destination: str
    status: str = Field(description="Current state: 'In Transit', 'Delayed', 'Rerouted'")
    eta: str
    operational_cost: float
    partner_reliability: float = Field(description="Score from 0.0 to 1.0")


class Alert(BaseModel):
    id: str
    type: str = Field(description="e.g., 'Port Strike', 'Weather Delay', 'Piracy'")
    location: str
    severity: str = Field(description="'High', 'Medium', 'Low'")
    description: str


# --- LangGraph State Definition ---

class AgentState(TypedDict):
    # 'messages' keeps a chat history/log of what the LLM is thinking
    # add_messages appends new messages instead of overwriting the list
    messages: Annotated[list[AnyMessage], add_messages]

    # Environment data (The "Observe" phase populates these)
    shipments: List[Shipment]
    alerts: List[Alert]

    # Agent's internal thought process
    hypothesis: str  # Populated by the 'Reason' node
    decision: str  # Populated by the 'Decide' node
    action_taken: str  # Populated by the 'Act' node


# --- Command Line Testing ---

if __name__ == "__main__":
    import json

    # 1. Create a mock shipment
    test_shipment = Shipment(
        id="SHP-90210",
        origin="Mumbai",
        destination="Dubai",
        status="In Transit",
        eta="2026-03-10",
        operational_cost=4500.00,
        partner_reliability=0.85
    )

    # 2. Create a mock alert based on your notebook
    test_alert = Alert(
        id="ALT-001",
        type="Port Strike",
        location="Strait of Hormuz",
        severity="High",
        description="Complete blockage due to sudden port strike. Major delays expected."
    )

    # 3. Initialize the LangGraph State
    initial_state: AgentState = {
        "messages": [],
        "shipments": [test_shipment],
        "alerts": [test_alert],
        "hypothesis": "",
        "decision": "",
        "action_taken": ""
    }

    # Print results to terminal
    print("=== Testing Pydantic Models ===")
    print(f"Shipment Data:\n{test_shipment.model_dump_json(indent=2)}")
    print(f"\nAlert Data:\n{test_alert.model_dump_json(indent=2)}")

    print("\n=== Testing Agent State ===")
    print(f"State Keys: {list(initial_state.keys())}")
    print(f"Number of active shipments in state: {len(initial_state['shipments'])}")
    print(f"Number of active alerts in state: {len(initial_state['alerts'])}")
    print("\n✅ state.py is working correctly!")