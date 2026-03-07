import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from state import AgentState, Shipment, Alert

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def observe(state: AgentState):
    # SPECIFIC AGENT CALL: Only look at affected shipments
    at_risk_shipments = [s for s in state.get("shipments", []) if s.status == "At Risk"]

    if not at_risk_shipments:
        return {"messages": [SystemMessage(content="System normal. No shipments currently at risk.")]}

    context = "AFFECTED SHIPMENTS AT RISK:\n"
    for s in at_risk_shipments:
        context += f"- ID: {s.shipment_id} | Route: {s.origin} -> {s.destination} | Risk: {s.delay_probability}\n"

    context += "\nACTIVE ALERTS CAUSING RISK:\n"
    for a in state.get("alerts", []):
        context += f"- SEVERITY: {a.severity} | Type: {a.type} | Loc: {a.location} | Details: {a.description}\n"

    return {"messages": [SystemMessage(content=f"System Context Gathered:\n{context}")]}


def reason(state: AgentState):
    messages = state.get("messages", [])
    if "System normal" in messages[0].content:
        return {"hypothesis": "All systems operational.", "messages": messages}

    prompt = HumanMessage(content=(
        "Identify the core risk to the affected shipments based on the context. "
        "Formulate a specific hypothesis about the cascading failures. Keep it to 2 concise sentences."
    ))
    response = llm.invoke(messages + [prompt])
    return {"hypothesis": response.content, "messages": messages + [response]}


def decide(state: AgentState):
    hypothesis = state.get("hypothesis", "")
    messages = state.get("messages", [])
    alerts = state.get("alerts", [])

    if hypothesis == "All systems operational.":
        return {"decision": "Maintain current routes.", "messages": messages}

    # Deterministically find the highest severity among active alerts
    highest_severity = "Low"
    for a in alerts:
        if a.severity == "High":
            highest_severity = "High"
            break
        elif a.severity == "Medium":
            highest_severity = "Medium"

    # Force the LLM to acknowledge the exact severity level
    prompt = HumanMessage(content=(
        f"Hypothesis: {hypothesis}\n"
        f"SYSTEM DATA: The current highest alert severity is strictly classified as '{highest_severity}'.\n"
        "Formulate a mitigation decision (e.g., reroute, switch carrier). \n"
        "CRITICAL RULE: If the system data says the severity is 'High', you MUST include the exact text '[NEEDS APPROVAL]' in your decision. "
        "If the system data says the severity is 'Medium' or 'Low', you are authorized to act autonomously and MUST NOT include '[NEEDS APPROVAL]'. "
        "Output only the final decision plan."
    ))

    response = llm.invoke(messages + [prompt])
    return {"decision": response.content, "messages": messages + [response]}


def act(state: AgentState):
    decision = state.get("decision", "")
    updated_shipments = state.get("shipments", []).copy()

    if "Maintain current routes" in decision:
        return {"action_taken": "Monitored situation. No action needed.", "shipments": updated_shipments}

    needs_approval = "[NEEDS APPROVAL]" in decision.upper()
    action_log = ""
    affected_count = 0

    for shipment in updated_shipments:
        if shipment.status == "At Risk":
            affected_count += 1
            if needs_approval:
                shipment.status = "Pending Approval"
                action_log = f"Drafted plans for {affected_count} shipments. Escalated to human operator (HIGH severity)."
            else:
                shipment.status = "Rerouted (Auto)"
                shipment.delay_probability = 0.1
                action_log = f"Autonomously rerouted {affected_count} shipments to bypass disruption."

    return {"action_taken": action_log, "shipments": updated_shipments}


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

app = workflow.compile()