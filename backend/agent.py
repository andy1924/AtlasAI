import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# Import the state models we just built
from state import AgentState, Shipment, Alert

# Load environment variables (Make sure OPENAI_API_KEY is in your .env)
load_dotenv()

# Initialize the LLM - gpt-4o-mini is perfect for fast, cheap hackathon iterations
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# --- Define the Agent Nodes ---

def observe(state: AgentState):
    print("\n👀 [OBSERVE] Gathering live logistics and news data...")

    context = "CURRENT SHIPMENTS:\n"
    for s in state.get("shipments", []):
        # Updated to use shipment_id, carrier, eta_hours, and delay_probability
        context += f"- ID: {s.shipment_id} | Route: {s.origin} -> {s.destination} | Carrier: {s.carrier} | Status: {s.status} | ETA (hrs): {s.eta_hours} | Delay Risk: {s.delay_probability}\n"

    context += "\nACTIVE ALERTS:\n"
    for a in state.get("alerts", []):
        context += f"- SEVERITY: {a.severity} | Type: {a.type} | Loc: {a.location} | Details: {a.description}\n"

    return {"messages": [SystemMessage(content=f"System Context Gathered:\n{context}")]}


def reason(state: AgentState):
    print("🧠 [REASON] Analyzing risks and forming hypothesis...")
    messages = state.get("messages", [])

    prompt = HumanMessage(content=(
        "Based on the system context, identify any risks, bottlenecks, or cascading failures. "
        "Formulate a specific hypothesis about what will go wrong if no action is taken. "
        "Keep it to 2-3 concise sentences."
    ))

    response = llm.invoke(messages + [prompt])
    return {"hypothesis": response.content, "messages": [response]}


def decide(state: AgentState):
    print("⚖️ [DECIDE] Formulating action plan...")
    hypothesis = state.get("hypothesis", "")
    messages = state.get("messages", [])

    prompt = HumanMessage(content=(
        f"Hypothesis: {hypothesis}\n"
        "Decide how to balance delivery time, operational costs, and partner reliability. "
        "Formulate a concrete decision (e.g., reroute, adjust schedule, escalate). "
        "Output ONLY the final decision plan."
    ))

    response = llm.invoke(messages + [prompt])
    return {"decision": response.content, "messages": [response]}


def act(state: AgentState):
    print("🚀 [ACT] Executing decisions and updating state...")
    decision = state.get("decision", "")
    updated_shipments = state.get("shipments", []).copy()

    action_log = "Monitored situation. No immediate action required."

    if "reroute" in decision.lower() or "divert" in decision.lower():
        for shipment in updated_shipments:
            if shipment.status == "In Transit":
                shipment.status = "Rerouted (Mitigation Active)"
                # Updated id to shipment_id
                action_log = f"System automatically rerouted shipment {shipment.shipment_id}."

    return {"action_taken": action_log, "shipments": updated_shipments}


# --- Build the LangGraph ---

workflow = StateGraph(AgentState)

workflow.add_node("observe", observe)
workflow.add_node("reason", reason)
workflow.add_node("decide", decide)
workflow.add_node("act", act)

workflow.add_edge(START, "observe")
workflow.add_edge("observe", "reason")
workflow.add_edge("reason", "decide")
workflow.add_edge("decide", "act")
workflow.add_edge("act", END)

# Compile the graph into a runnable application
app = workflow.compile()

# --- Command Line Testing ---

if __name__ == "__main__":
    # 1. Setup Mock Data (Same as state.py)
    test_shipment = Shipment(
        id="SHP-90210", origin="Mumbai", destination="Dubai",
        status="In Transit", eta="2026-03-10",
        operational_cost=4500.00, partner_reliability=0.85
    )
    test_alert = Alert(
        id="ALT-001", type="Port Strike", location="Dubai",
        severity="High", description="Complete blockage due to sudden port strike. Major delays expected."
    )

    initial_state: AgentState = {
        "messages": [],
        "shipments": [test_shipment],
        "alerts": [test_alert],
        "hypothesis": "",
        "decision": "",
        "action_taken": ""
    }

    # 2. Run the graph
    print("=== Starting Autonomous Logistics Agent ===")

    # stream() lets us see the output of each node as it finishes
    for output in app.stream(initial_state):
        for node_name, state_update in output.items():
            if node_name == "reason":
                print(f"\n   -> HYPOTHESIS: {state_update.get('hypothesis')}")
            elif node_name == "decide":
                print(f"\n   -> DECISION: {state_update.get('decision')}")
            elif node_name == "act":
                print(f"\n   -> ACTION TAKEN: {state_update.get('action_taken')}")
                print(f"   -> NEW SHIPMENT STATUS: {state_update.get('shipments')[0].status}")

    print("\n✅ Cycle Complete!")