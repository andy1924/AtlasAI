from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import json
import os
from memory import add_learned_action
from state import Shipment, Alert, AgentState
from agent import app as agent_app

app = FastAPI(title="Cyber Cypher Logistics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load Global In-Memory State from JSON ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "maindata", "simulated_shipments.json")

current_shipments = []
current_alerts = []
agent_history = []

try:
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)
        current_shipments = [Shipment(**item) for item in data]
    print(f"✅ Successfully loaded {len(current_shipments)} shipments.")
except Exception as e:
    print(f"❌ Error loading JSON: {e}")


# --- API Endpoints ---

@app.get("/api/shipments")
def get_shipments():
    return {"shipments": current_shipments}


@app.get("/api/alerts")
def get_alerts():
    return {"alerts": current_alerts}


class ChaosRequest(BaseModel):
    type: str
    location: str
    severity: str  # Ensure this is here
    description: str


@app.post("/api/trigger-chaos")
def trigger_chaos(chaos: ChaosRequest):
    global current_shipments, current_alerts

    # 1. Add the new alert with the CORRECT severity from the frontend
    new_alert = Alert(
        id=f"ALT-{len(current_alerts) + 1:03d}",
        type=chaos.type,
        location=chaos.location,
        severity=chaos.severity,  # <--- This fixes the "Always High" bug
        description=chaos.description
    )
    current_alerts.append(new_alert)

    # 2. Flag affected shipments instantly
    for shipment in current_shipments:
        if shipment.origin == chaos.location or shipment.destination == chaos.location:
            shipment.status = "At Risk"
            shipment.delay_probability = 0.95

    return {"message": "Chaos injected!", "alert": new_alert}


@app.post("/api/run-agent")
def run_agent():
    global current_shipments

    initial_state: AgentState = {
        "messages": [],
        "shipments": current_shipments,
        "alerts": current_alerts,
        "hypothesis": "",
        "decision": "",
        "action_taken": ""
    }

    final_state = agent_app.invoke(initial_state)
    current_shipments = final_state.get("shipments", current_shipments)

    log_entry = {
        "hypothesis": final_state.get("hypothesis"),
        "decision": final_state.get("decision"),
        "action_taken": final_state.get("action_taken")
    }
    agent_history.insert(0, log_entry)  # Put newest log at the top

    return {
        "message": "Agent cycle complete.",
        "log": log_entry,
        "updated_shipments": current_shipments
    }


@app.post("/api/approve-actions")
def approve_actions():
    """Human-in-the-loop endpoint. Approves actions AND triggers the ChromaDB Learn loop."""
    global current_shipments, current_alerts
    count = 0

    for shipment in current_shipments:
        if shipment.status == "Pending Approval":
            shipment.status = "Rerouted (Approved)"
            shipment.delay_probability = 0.05
            count += 1

    action_taken_text = f"Officially executed rerouting for {count} high-risk shipments based on human operator validation."

    # --- THE LEARN LOOP ---
    if current_alerts:
        latest_alert = current_alerts[-1]
        add_learned_action(
            alert_description=latest_alert.description,
            severity=latest_alert.severity,
            action_taken=action_taken_text
        )

    agent_history.insert(0, {
        "hypothesis": "Human Operator Override",
        "decision": "Reviewed and approved escalated AI mitigation plans.",
        "action_taken": action_taken_text
    })

    return {"message": f"Approved {count} actions.", "updated_shipments": current_shipments}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)