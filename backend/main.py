from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

# Import our state models and the compiled LangGraph agent
from state import Shipment, Alert, AgentState
from agent import app as agent_app

app = FastAPI(title="Cyber Cypher Logistics API")

# Allow the Next.js frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For the hackathon, allow all. Restrict in prod!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add these imports at the top of backend/main.py if not there
import json
import os

# --- Load Global In-Memory State from JSON ---

# This dynamically finds your maindata folder regardless of where you run the script from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "maindata", "stimulated_shipments.json")

current_shipments = []

try:
    with open(JSON_PATH, "r") as file:
        data = json.load(file)
        # Convert raw JSON dicts into Pydantic Shipment objects
        current_shipments = [Shipment(**item) for item in data]
    print(f"✅ Successfully loaded {len(current_shipments)} shipments from JSON.")
except FileNotFoundError:
    print(f"❌ Error: Could not find JSON file at {JSON_PATH}")
except Exception as e:
    print(f"❌ Error parsing JSON: {e}")

# (Keep your current_alerts and agent_history lists exactly as they are)
current_alerts = []
agent_history = []  # Stores the reasoning logs for the UI


# --- API Endpoints ---

@app.get("/api/shipments")
def get_shipments():
    """Fetch the live logistics status."""
    return {"shipments": current_shipments}


@app.get("/api/alerts")
def get_alerts():
    """Fetch active news or system alerts."""
    return {"alerts": current_alerts}


@app.get("/api/agent-history")
def get_history():
    """Fetch the agent's thought process for the UI log."""
    return {"history": agent_history}


class ChaosRequest(BaseModel):
    type: str
    location: str
    description: str


@app.post("/api/trigger-chaos")
def trigger_chaos(chaos: ChaosRequest):
    """The 'Chaos Button' endpoint to inject a fake alert."""
    new_alert = Alert(
        id=f"ALT-{len(current_alerts) + 1:03d}",
        type=chaos.type,
        location=chaos.location,
        severity="High",
        description=chaos.description
    )
    current_alerts.append(new_alert)
    return {"message": "Chaos injected successfully!", "alert": new_alert}


@app.post("/api/run-agent")
def run_agent():
    """Triggers the LangGraph Observe -> Reason -> Decide -> Act loop."""
    global current_shipments

    initial_state: AgentState = {
        "messages": [],
        "shipments": current_shipments,
        "alerts": current_alerts,
        "hypothesis": "",
        "decision": "",
        "action_taken": ""
    }

    # Run the graph
    final_state = agent_app.invoke(initial_state)

    # Update our global state with the agent's actions
    current_shipments = final_state.get("shipments", current_shipments)

    # Log the thought process for the frontend UI
    log_entry = {
        "hypothesis": final_state.get("hypothesis"),
        "decision": final_state.get("decision"),
        "action_taken": final_state.get("action_taken")
    }
    agent_history.append(log_entry)

    return {
        "message": "Agent cycle complete.",
        "log": log_entry,
        "updated_shipments": current_shipments
    }


# --- Command Line Testing ---

if __name__ == "__main__":
    print("🚀 Starting Cyber Cypher Backend on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)